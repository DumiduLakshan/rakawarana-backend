import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.services.posts_service import (
    create_rescue_post_with_images,
    get_priority_stats,
    list_top_critical_posts,
    list_rescue_posts_with_images,
    list_rescue_posts_filtered,
)
from app.utils.spaces_client import get_spaces_client
from app.utils.supabase_client import get_supabase

router = APIRouter(prefix="/posts", tags=["posts"])
logger = logging.getLogger(__name__)


@router.post("", summary="Create a rescue post with images")
async def create_rescue_post(
    images: list[UploadFile] = File(...),
    supabase_client=Depends(get_supabase),
    full_name: str = Form(...),
    phone_number: str = Form(...),
    alt_phone_number: str | None = Form(None),
    location: str = Form(...),
    land_mark: str | None = Form(None),
    district: str | None = Form(None),
    emergency_type: str = Form(...),
    number_of_peoples_to_rescue: int | None = Form(None),
    number_of_peoples: int | None = Form(None),
    is_medical_needed: bool = Form(False),
    water_level: str | None = Form(None),
    safe_hours: int | None = Form(None),
    need_foods: bool = Form(False),
    need_water: bool = Form(False),
    need_transport: bool = Form(False),
    need_medic: bool = Form(False),
    need_power: bool = Form(False),
    need_clothes: bool = Form(False),
    description: str | None = Form(None),
    priority_level: str = Form(...),
    location_url: str = Form(...),
):
    spaces_client = get_spaces_client()

    people_count = (
        number_of_peoples_to_rescue
        if number_of_peoples_to_rescue is not None
        else number_of_peoples
    )

    payload = {
        "full_name": full_name,
        "phone_number": phone_number,
        "alt_phone_number": alt_phone_number,
        "location": location,
        "land_mark": land_mark,
        "district": district,
        "emergency_type": emergency_type,
        "number_of_peoples_to_rescue": people_count,
        "is_medical_needed": is_medical_needed,
        "water_level": water_level,
        "safe_hours": safe_hours,
        "need_foods": need_foods,
        "need_water": need_water,
        "need_transport": need_transport,
        "need_medic": need_medic,
        "need_power": need_power,
        "need_clothes": need_clothes,
        "description": description,
        "priority_level": priority_level,
        "location_url": location_url,
    }

    result = await create_rescue_post_with_images(
        payload=payload,
        files=images,
        supabase_client=supabase_client,
        spaces_client=spaces_client,
    )
    return result


@router.get("", summary="List rescue posts with images")
def list_rescue_posts(supabase_client=Depends(get_supabase)):
    return list_rescue_posts_with_images(supabase_client)


@router.get(
    "/critical/top",
    summary="List most critical rescue posts (top 3) with images",
)
def list_critical_posts(supabase_client=Depends(get_supabase)):
    return list_top_critical_posts(supabase_client)


@router.get(
    "/filter",
    summary="Filter rescue posts by multiple criteria (AND) with images",
)
def filter_rescue_posts(
    supabase_client=Depends(get_supabase),
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
):
    return list_rescue_posts_filtered(
        supabase_client=supabase_client,
        district=district,
        emergency_type=emergency_type,
        water_level=water_level,
        is_medical_needed=is_medical_needed,
        need_foods=need_foods,
        need_water=need_water,
        need_transport=need_transport,
        need_medic=need_medic,
        need_power=need_power,
        need_clothes=need_clothes,
        is_verified=is_verified,
        min_people=min_people,
        max_safe_hours=max_safe_hours,
    )


@router.get(
    "/stats",
    summary="Get post statistics (total, high, medium, low priority)",
)
def get_post_stats(supabase_client=Depends(get_supabase)):
    return get_priority_stats(supabase_client)
