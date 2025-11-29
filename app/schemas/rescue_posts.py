from typing import Any, Iterable

from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic import ConfigDict
from fastapi import Form

from app.utils.exception_handlers import InvalidDataException


def _validate_phone(number: str, field_name: str) -> str:
    digits = "".join(ch for ch in number if ch.isdigit())
    if len(digits) < 7 or len(digits) > 15:
        raise InvalidDataException(
            message=f"{field_name.replace('_', ' ').title()} must have 7-15 digits",
            details={"field": field_name},
        )
    return digits


def _validate_urls(urls: Iterable[str]) -> list[str]:
    cleaned: list[str] = []
    for url in urls:
        stripped = url.strip()
        if not stripped:
            continue
        if not (stripped.startswith("http://") or stripped.startswith("https://")):
            raise InvalidDataException(
                message="Image URLs must start with http:// or https://",
                details={"field": "image_urls", "value": url},
            )
        cleaned.append(stripped)

    if not cleaned:
        raise InvalidDataException(
            message="At least one image URL is required when images are provided",
            details={"field": "image_urls"},
        )
    return cleaned


def _validate_url(url: str, field_name: str) -> str:
    stripped = url.strip()
    if not stripped:
        raise InvalidDataException(
            message=f"{field_name.replace('_', ' ').title()} is required",
            details={"field": field_name},
        )
    if not (stripped.startswith("http://") or stripped.startswith("https://")):
        raise InvalidDataException(
            message=f"{field_name.replace('_', ' ').title()} must start with http:// or https://",
            details={"field": field_name, "value": url},
        )
    return stripped


class RescuePostCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    full_name: str = Field(..., min_length=3, max_length=150)
    phone_number: str = Field(..., min_length=7, max_length=20)
    alt_phone_number: str | None = Field(None, min_length=7, max_length=20)
    location: str = Field(..., min_length=3, max_length=255)
    land_mark: str | None = Field(None, max_length=255)
    district: str | None = Field(None, max_length=100)
    emergency_type: str = Field(..., min_length=3, max_length=100)
    priority_level: str = Field(..., min_length=3, max_length=20)
    number_of_peoples_to_rescue: int | None = Field(
        None, ge=1, le=10_000, alias="number_of_peoples"
    )
    is_medical_needed: bool = False
    water_level: str | None = Field(None, max_length=50)
    safe_hours: int | None = Field(None, ge=0, le=1_000)
    need_foods: bool = False
    need_water: bool = False
    need_transport: bool = False
    need_medic: bool = False
    need_power: bool = False
    need_clothes: bool = False
    description: str | None = Field(None, max_length=2_000)
    location_url: str = Field(..., min_length=5, max_length=2_048)
    image_urls: list[str] | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_primary_phone(cls, value: str) -> str:
        return _validate_phone(value, "phone_number")

    @field_validator("alt_phone_number")
    @classmethod
    def validate_alt_phone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_phone(value, "alt_phone_number")

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        return _validate_urls(value)

    @field_validator("priority_level")
    @classmethod
    def validate_priority_level(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed = {"high", "medium", "low"}
        if normalized not in allowed:
            raise InvalidDataException(
                message="Priority level must be one of high, medium, or low",
                details={"field": "priority_level", "value": value},
            )
        return normalized

    @field_validator("location_url")
    @classmethod
    def validate_location_url(cls, value: str) -> str:
        return _validate_url(value, "location_url")

    @classmethod
    def validate_with_app_error(cls, data: dict[str, Any]) -> "RescuePostCreate":
        """Validate input and raise our InvalidDataException for consistency."""
        try:
            return cls.model_validate(data)
        except ValidationError as exc:
            formatted_errors = _format_pydantic_errors(exc.errors())
            raise InvalidDataException(
                message="Invalid rescue post data",
                details={"errors": formatted_errors},
            ) from exc

    @classmethod
    def as_form(
        cls,
        full_name: str = Form(...),
        phone_number: str = Form(...),
        alt_phone_number: str | None = Form(None),
        location: str = Form(...),
        land_mark: str | None = Form(None),
        district: str | None = Form(None),
        emergency_type: str = Form(...),
        number_of_peoples_to_rescue: int | None = Form(None),
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
    ) -> "RescuePostCreate":
        """Enable FastAPI to parse form-data directly into the schema."""
        return cls(
            full_name=full_name,
            phone_number=phone_number,
            alt_phone_number=alt_phone_number,
            location=location,
            land_mark=land_mark,
            district=district,
            emergency_type=emergency_type,
            number_of_peoples_to_rescue=number_of_peoples_to_rescue,
            is_medical_needed=is_medical_needed,
            water_level=water_level,
            safe_hours=safe_hours,
            need_foods=need_foods,
            need_water=need_water,
            need_transport=need_transport,
            need_medic=need_medic,
            need_power=need_power,
            need_clothes=need_clothes,
            description=description,
            priority_level=priority_level,
            location_url=location_url,
        )


def _format_pydantic_errors(errors: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Convert Pydantic errors into simpler {field, message} pairs for frontend."""
    formatted: list[dict[str, str]] = []
    for err in errors:
        loc_parts = [str(part) for part in err.get("loc", []) if part != "__root__"]
        field = ".".join(loc_parts) if loc_parts else "unknown"
        message = _friendly_message(err)
        formatted.append({"field": field, "message": message})
    return formatted


def _friendly_message(err: dict[str, Any]) -> str:
    err_type = err.get("type")
    ctx = err.get("ctx") or {}
    msg = err.get("msg", "Invalid value")

    if err_type == "string_too_short" and "min_length" in ctx:
        return f"Must be at least {ctx['min_length']} characters long"
    if err_type == "string_too_long" and "max_length" in ctx:
        return f"Must be at most {ctx['max_length']} characters long"
    if err_type == "greater_than_equal" and "ge" in ctx:
        return f"Must be greater than or equal to {ctx['ge']}"
    if err_type == "less_than_equal" and "le" in ctx:
        return f"Must be less than or equal to {ctx['le']}"

    return msg
