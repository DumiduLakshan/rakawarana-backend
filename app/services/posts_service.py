import logging
import mimetypes
import os
from typing import Any
from uuid import uuid4

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile

from app.repositories.posts_repository import (
    fetch_rescue_posts_by_district,
    fetch_rescue_posts_by_emergency_type,
    fetch_rescue_posts_by_water_level,
    fetch_rescue_posts_with_images,
    fetch_rescue_posts_filtered,
    fetch_priority_counts,
    fetch_unverified_posts,
    verify_rescue_post,
    delete_rescue_post,
    insert_images,
    insert_rescue_post,
)
from app.schemas.rescue_posts import RescuePostCreate
from app.utils.exception_handlers import AppError, InvalidDataException
from app.utils.settings import get_settings
from app.utils.telegram import send_telegram_notification

logger = logging.getLogger(__name__)


async def upload_images_to_spaces(
    files: list[UploadFile], spaces_client, settings
) -> list[str]:
    if not files:
        raise InvalidDataException(
            message="At least one image file is required",
            details={"field": "images"},
        )

    max_bytes = settings.digitalocean_max_file_size_mb * 1024 * 1024
    cdn_urls: list[str] = []

    for upload in files:
        if not upload.filename:
            raise InvalidDataException(
                message="Image file must have a filename",
                details={"field": "images"},
            )

        content_type = upload.content_type or mimetypes.guess_type(upload.filename)[0]
        if not content_type or not content_type.startswith("image/"):
            raise InvalidDataException(
                message="Only image uploads are allowed",
                details={"field": "images", "filename": upload.filename},
            )

        content = await upload.read()
        if not content:
            raise InvalidDataException(
                message="Image file is empty",
                details={"field": "images", "filename": upload.filename},
            )

        if len(content) > max_bytes:
            raise InvalidDataException(
                message=f"Image file exceeds {settings.digitalocean_max_file_size_mb}MB",
                details={"field": "images", "filename": upload.filename},
            )

        _, ext = os.path.splitext(upload.filename)
        object_name = f"{uuid4().hex}{ext or ''}"
        key = (
            f"{settings.digitalocean_upload_prefix}/{object_name}"
            if settings.digitalocean_upload_prefix
            else object_name
        )

        try:
            spaces_client.put_object(
                Bucket=settings.digitalocean_bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
                ACL="public-read",
            )
        except (BotoCoreError, ClientError) as exc:
            logger.exception("Failed to upload image to Spaces: %s", upload.filename)
            raise AppError(
                message="Failed to upload image",
                status_code=500,
                details={"filename": upload.filename},
            ) from exc

        cdn_urls.append(f"{settings.digitalocean_cdn_endpoint}/projectrakawarananew/{key}")

    return cdn_urls


async def create_rescue_post_with_images(
    payload: dict[str, Any],
    files: list[UploadFile],
    supabase_client,
    spaces_client,
) -> dict[str, Any]:
    settings = get_settings()
    validated = RescuePostCreate.validate_with_app_error(
        {k: v for k, v in payload.items() if v is not None}
    )

    image_urls = await upload_images_to_spaces(files, spaces_client, settings)

    post_payload = validated.model_dump(exclude={"image_urls"})
    post_payload["phone_number"] = int(validated.phone_number)
    if validated.alt_phone_number is not None:
        post_payload["alt_phone_number"] = int(validated.alt_phone_number)

    post_record = insert_rescue_post(supabase_client, post_payload)

    images_payload = [
        {"image_url": url, "post_id": post_record["id"]} for url in image_urls
    ]
    image_records = insert_images(supabase_client, images_payload)

    # Notify via Telegram (best-effort)
    await send_telegram_notification(
        text_fields={
            "Full Name": validated.full_name,
            "Phone": validated.phone_number,
            "Alt Phone": validated.alt_phone_number,
            "Location": validated.location,
            "Land Mark": validated.land_mark,
            "District": validated.district,
            "Emergency Type": validated.emergency_type,
            "Priority Level": validated.priority_level,
            "Location URL": validated.location_url,
            "Description": validated.description,
        },
        image_urls=image_urls,
        is_verified=False,
    )

    logger.info("Created rescue post %s with %d images", post_record.get("id"), len(image_records))
    return {"post": post_record, "images": image_records}


def list_rescue_posts_with_images(supabase_client) -> list[dict[str, Any]]:
    """Return posts with their related images."""
    return fetch_rescue_posts_with_images(supabase_client)


def list_rescue_posts_by_emergency(
    supabase_client, emergency_type: str
) -> list[dict[str, Any]]:
    """Return posts filtered by emergency_type with their images."""
    if not emergency_type:
        raise InvalidDataException(
            message="Emergency type is required", details={"field": "emergency_type"}
        )
    return fetch_rescue_posts_by_emergency_type(supabase_client, emergency_type)


def list_rescue_posts_by_district(
    supabase_client, district: str
) -> list[dict[str, Any]]:
    """Return posts filtered by district with their images."""
    if not district:
        raise InvalidDataException(
            message="District is required", details={"field": "district"}
        )
    return fetch_rescue_posts_by_district(supabase_client, district)


def list_rescue_posts_by_water_level(
    supabase_client, water_level: str
) -> list[dict[str, Any]]:
    """Return posts filtered by water_level with their images."""
    if not water_level:
        raise InvalidDataException(
            message="Water level is required", details={"field": "water_level"}
        )
    return fetch_rescue_posts_by_water_level(supabase_client, water_level)


def list_rescue_posts_filtered(
    supabase_client,
    district: str | None = None,
    emergency_type: str | None = None,
    water_level: str | None = None,
    is_medical_needed: bool | None = None,
    need_foods: bool | None = None,
    need_water: bool | None = None,
    need_transport: bool | None = None,
    need_medic: bool | None = None,
    need_power: bool | None = None,
    need_clothes: bool | None = None,
    is_verified: bool | None = None,
    min_people: int | None = None,
    max_safe_hours: int | None = None,
) -> list[dict[str, Any]]:
    """Return posts filtered by any combination of provided filters (AND logic)."""
    filters = {
        "district": district,
        "emergency_type": emergency_type,
        "water_level": water_level,
        "is_medical_needed": is_medical_needed,
        "need_foods": need_foods,
        "need_water": need_water,
        "need_transport": need_transport,
        "need_medic": need_medic,
        "need_power": need_power,
        "need_clothes": need_clothes,
        "is_verified": is_verified,
        "min_people": min_people,
        "max_safe_hours": max_safe_hours,
    }

    if all(v is None for v in filters.values()):
        raise InvalidDataException(
            message="At least one filter must be provided",
            details={"fields": list(filters.keys())},
        )

    return fetch_rescue_posts_filtered(supabase_client, filters)


def get_priority_stats(supabase_client) -> dict[str, int]:
    """Return counts for total/high/medium/low priority posts."""
    return fetch_priority_counts(supabase_client)


def list_unverified_posts(supabase_client) -> list[dict[str, Any]]:
    """Return unverified posts with images."""
    return fetch_unverified_posts(supabase_client)


def verify_post(supabase_client, post_id: str) -> dict[str, Any]:
    """Mark a post as verified."""
    if not post_id:
        raise InvalidDataException(
            message="Post id is required", details={"field": "post_id"}
        )
    return verify_rescue_post(supabase_client, post_id)


def delete_post(supabase_client, post_id: str) -> None:
    """Delete a post by id."""
    if not post_id:
        raise InvalidDataException(
            message="Post id is required", details={"field": "post_id"}
        )
    delete_rescue_post(supabase_client, post_id)


def _priority_score(post: dict[str, Any]) -> tuple[float, float]:
    """Compute a priority score; higher is more critical. Returns (score, -timestamp)."""
    score = 0.0

    # More people => higher priority
    people = post.get("number_of_peoples_to_rescue") or 0
    score += min(people, 50) * 2.0  # cap to avoid runaway

    # Water level severity mapping
    water_level = (post.get("water_level") or "").lower()
    water_map = {
        "head": 9,
        "neck": 8,
        "chest": 7,
        "shoulder": 6,
        "waist": 5,
        "knee": 3,
        "ankle": 1,
    }
    score += water_map.get(water_level, 0)

    # Medical need is high priority
    if post.get("is_medical_needed"):
        score += 10
    if post.get("need_medic"):
        score += 6

    # Aggregate needs
    needs = [
        "need_foods",
        "need_water",
        "need_transport",
        "need_power",
        "need_clothes",
    ]
    for need in needs:
        if post.get(need):
            score += 2

    # Safe hours: low remaining safe hours => more urgent
    safe_hours = post.get("safe_hours")
    if isinstance(safe_hours, int):
        if safe_hours <= 1:
            score += 6
        elif safe_hours <= 4:
            score += 4
        elif safe_hours <= 12:
            score += 2

    # is_verified could indicate confirmed severity
    if post.get("is_verified"):
        score += 1

    # Use created_at to break ties (older first)
    created_at = post.get("created_at") or ""
    tie_breaker = 0.0
    try:
        # Convert ISO string to timestamp; earlier => higher priority via negative
        tie_breaker = -float(
            __import__("datetime")
            .datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            .timestamp()
        )
    except Exception:
        tie_breaker = 0.0

    return score, tie_breaker


def list_top_critical_posts(supabase_client, limit: int = 3) -> list[dict[str, Any]]:
    """Return top critical posts (with images) based on priority scoring."""
    posts = fetch_rescue_posts_with_images(supabase_client)
    sorted_posts = sorted(posts, key=_priority_score, reverse=True)
    return sorted_posts[:limit]
