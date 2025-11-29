import logging
from typing import Any

from postgrest.exceptions import APIError
from supabase import Client

from app.utils.exception_handlers import AppError

logger = logging.getLogger(__name__)


def insert_rescue_post(supabase: Client, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        response = supabase.table("rescue_posts").insert(payload).execute()
    except APIError as exc:
        logger.error("Failed to insert rescue_post: %s", exc)
        raise AppError(
            message="Failed to save rescue post",
            status_code=500,
            details={"error": str(exc)},
        ) from exc

    if not response.data:
        raise AppError(
            message="Failed to save rescue post",
            status_code=500,
            details={"error": "No data returned from insert"},
        )

    return response.data[0]


def insert_images(
    supabase: Client, images_payload: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not images_payload:
        return []

    try:
        response = supabase.table("images").insert(images_payload).execute()
    except APIError as exc:
        logger.error("Failed to insert images: %s", exc)
        raise AppError(
            message="Failed to save images",
            status_code=500,
            details={"error": str(exc)},
        ) from exc

    if not response.data:
        raise AppError(
            message="Failed to save images",
            status_code=500,
            details={"error": "No data returned from insert"},
        )
    return response.data


def fetch_rescue_posts_with_images(
    supabase: Client,
) -> list[dict[str, Any]]:
    try:
        response = (
            supabase.table("rescue_posts")
            .select("*, images(*)")
            .order("created_at", desc=True)
            .execute()
        )
    except APIError as exc:
        logger.error("Failed to fetch rescue posts: %s", exc)
        raise AppError(
            message="Failed to fetch rescue posts",
            status_code=500,
            details={"error": str(exc)},
        ) from exc

    return response.data or []


def fetch_rescue_posts_by_emergency_type(
    supabase: Client, emergency_type: str
) -> list[dict[str, Any]]:
    try:
        response = (
            supabase.table("rescue_posts")
            .select("*, images(*)")
            .eq("emergency_type", emergency_type)
            .order("created_at", desc=True)
            .execute()
        )
    except APIError as exc:
        logger.error(
            "Failed to fetch rescue posts by emergency_type=%s: %s",
            emergency_type,
            exc,
        )
        raise AppError(
            message="Failed to fetch rescue posts",
            status_code=500,
            details={"error": str(exc), "emergency_type": emergency_type},
        ) from exc

    return response.data or []


def fetch_rescue_posts_by_district(supabase: Client, district: str) -> list[dict[str, Any]]:
    try:
        response = (
            supabase.table("rescue_posts")
            .select("*, images(*)")
            .eq("district", district)
            .order("created_at", desc=True)
            .execute()
        )
    except APIError as exc:
        logger.error(
            "Failed to fetch rescue posts by district=%s: %s",
            district,
            exc,
        )
        raise AppError(
            message="Failed to fetch rescue posts",
            status_code=500,
            details={"error": str(exc), "district": district},
        ) from exc

    return response.data or []


def fetch_rescue_posts_by_water_level(
    supabase: Client, water_level: str
) -> list[dict[str, Any]]:
    try:
        response = (
            supabase.table("rescue_posts")
            .select("*, images(*)")
            .eq("water_level", water_level)
            .order("created_at", desc=True)
            .execute()
        )
    except APIError as exc:
        logger.error(
            "Failed to fetch rescue posts by water_level=%s: %s",
            water_level,
            exc,
        )
        raise AppError(
            message="Failed to fetch rescue posts",
            status_code=500,
            details={"error": str(exc), "water_level": water_level},
        ) from exc

    return response.data or []


def fetch_rescue_posts_filtered(
    supabase: Client,
    filters: dict[str, Any],
) -> list[dict[str, Any]]:
    try:
        query = supabase.table("rescue_posts").select("*, images(*)")

        for field, value in filters.items():
            if value is None:
                continue
            if field == "min_people":
                query = query.gte("number_of_peoples_to_rescue", value)
            elif field == "max_safe_hours":
                query = query.lte("safe_hours", value)
            else:
                query = query.eq(field, value)

        response = query.order("created_at", desc=True).execute()
    except APIError as exc:
        logger.error("Failed to fetch filtered rescue posts: %s", exc)
        raise AppError(
            message="Failed to fetch rescue posts",
            status_code=500,
            details={"error": str(exc), "filters": filters},
        ) from exc

    return response.data or []


def fetch_priority_counts(supabase: Client) -> dict[str, int]:
    """Return counts for total and priority levels (high/medium/low via priority_level)."""
    try:
        total_resp = supabase.table("rescue_posts").select("id", count="exact").execute()
        total = total_resp.count or 0

        def count_for(level: str) -> int:
            resp = (
                supabase.table("rescue_posts")
                .select("id", count="exact")
                .eq("priority_level", level)
                .execute()
            )
            return resp.count or 0

        return {
            "total_posts": total,
            "high_priority_posts": count_for("high"),
            "medium_priority_posts": count_for("medium"),
            "low_priority_posts": count_for("low"),
        }
    except APIError as exc:
        logger.error("Failed to fetch priority counts: %s", exc)
        raise AppError(
            message="Failed to fetch post stats",
            status_code=500,
            details={"error": str(exc)},
        ) from exc


def fetch_unverified_posts(supabase: Client) -> list[dict[str, Any]]:
    try:
        response = (
            supabase.table("rescue_posts")
            .select("*, images(*)")
            .eq("is_verified", False)
            .order("created_at", desc=True)
            .execute()
        )
    except APIError as exc:
        logger.error("Failed to fetch unverified rescue posts: %s", exc)
        raise AppError(
            message="Failed to fetch rescue posts",
            status_code=500,
            details={"error": str(exc)},
        ) from exc

    return response.data or []


def verify_rescue_post(supabase: Client, post_id: str) -> dict[str, Any]:
    try:
        response = (
            supabase.table("rescue_posts")
            .update({"is_verified": True})
            .eq("id", post_id)
            .execute()
        )
    except APIError as exc:
        logger.error("Failed to verify rescue post %s: %s", post_id, exc)
        raise AppError(
            message="Failed to verify rescue post",
            status_code=500,
            details={"error": str(exc), "post_id": post_id},
        ) from exc

    if not response.data:
        raise AppError(
            message="Rescue post not found",
            status_code=404,
            details={"post_id": post_id},
        )

    return response.data[0]


def delete_rescue_post(supabase: Client, post_id: str) -> None:
    try:
        response = supabase.table("rescue_posts").delete().eq("id", post_id).execute()
    except APIError as exc:
        logger.error("Failed to delete rescue post %s: %s", post_id, exc)
        raise AppError(
            message="Failed to delete rescue post",
            status_code=500,
            details={"error": str(exc), "post_id": post_id},
        ) from exc

    if not response.data:
        raise AppError(
            message="Rescue post not found",
            status_code=404,
            details={"post_id": post_id},
        )
