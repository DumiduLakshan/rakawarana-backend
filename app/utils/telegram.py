import logging
from typing import Iterable

import httpx

from app.utils.settings import get_settings

logger = logging.getLogger(__name__)


def _format_html_message(data: dict[str, str | None], is_verified: bool | None) -> str:
    status = "✅ Verified" if is_verified else "❌ Not verified"
    parts = [
        "<b>🚨 New rescue post arrived</b>",
        f"<b>{status}</b>",
        "",
    ]
    field_icons = {
        "Full Name": "👤",
        "Phone": "📞",
        "Alt Phone": "📞",
        "Location": "📍",
        "Land Mark": "🏷️",
        "District": "🧭",
        "Emergency Type": "⚠️",
        "Description": "📝",
    }
    for label, value in data.items():
        if value:
            icon = field_icons.get(label, "•")
            parts.append(f"{icon} <b>{label}:</b> <code>{value}</code>")
    return "\n".join(parts)


async def send_telegram_notification(
    text_fields: dict[str, str | None],
    image_urls: Iterable[str] | None = None,
    is_verified: bool | None = None,
) -> None:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_channel_id:
        logger.info("Telegram credentials not configured; skipping notification")
        return

    base_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
    chat_id = settings.telegram_channel_id
    caption = _format_html_message(text_fields, is_verified)
    images = [url for url in (image_urls or []) if url]

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            if images:
                if len(images) == 1:
                    resp = await client.post(
                        f"{base_url}/sendPhoto",
                        json={
                            "chat_id": chat_id,
                            "photo": images[0],
                            "caption": caption,
                            "parse_mode": "HTML",
                        },
                    )
                else:
                    media = []
                    for idx, url in enumerate(images):
                        item = {"type": "photo", "media": url}
                        if idx == 0:
                            item["caption"] = caption
                            item["parse_mode"] = "HTML"
                        media.append(item)
                    resp = await client.post(
                        f"{base_url}/sendMediaGroup",
                        json={"chat_id": chat_id, "media": media},
                    )
            else:
                resp = await client.post(
                    f"{base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": caption,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    },
                )

            if resp.status_code >= 400:
                logger.error(
                    "Telegram notification failed (%s): %s",
                    resp.status_code,
                    resp.text,
                )
                # Fallback to sending a text message with URLs to ensure notification still arrives.
                urls_text = "\n".join(images) if images else ""
                fallback_text = caption
                if urls_text:
                    fallback_text = f"{caption}\n\nImages:\n{urls_text}"
                await client.post(
                    f"{base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": fallback_text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": False,
                    },
                )
        except Exception:
            logger.exception("Failed to send Telegram notification")
