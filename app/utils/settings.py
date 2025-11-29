import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

# Load environment variables from a local .env file if present.
load_dotenv()


@dataclass
class Settings:
    supabase_url: str
    supabase_key: str
    digitalocean_access_key: str
    digitalocean_secret_key: str
    digitalocean_bucket: str
    digitalocean_region: str
    digitalocean_cdn_endpoint: str
    digitalocean_origin_endpoint: str
    supabase_bucket: str = "images"
    digitalocean_upload_prefix: str = "posts_images"
    digitalocean_max_file_size_mb: int = 5
    admin_token: str | None = None
    telegram_bot_token: str | None = None
    telegram_channel_id: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv(
            "SUPABASE_ANON_KEY"
        )
        supabase_bucket = os.getenv("SUPABASE_BUCKET", "images")

        access_key = os.getenv("DIGITALOCEAN_ACCESS_KEY")
        secret_key = os.getenv("DIGITALOCEAN_SECRET_KEY")
        bucket = os.getenv("DIGITALOCEAN_BUCKET_NAME")
        region = os.getenv("DIGITALOCEAN_REGION") or os.getenv("DIGITALOCEAN_REIGION")
        cdn_endpoint = os.getenv("DIGITALOCEAN_CDN")
        origin_endpoint = os.getenv("DIGITALOCEAN_ORIGIN") or os.getenv(
            "DIGITALOCEAN_ORIGIN_ENDPOINT"
        )
        # Upload prefix; keep as-is (no forced nesting). Empty means root of the bucket.
        raw_upload_prefix = os.getenv("DIGITALOCEAN_UPLOAD_PREFIX", "").strip("/")
        normalized_prefix = raw_upload_prefix

        max_file_size_mb = int(os.getenv("DIGITALOCEAN_MAX_FILE_SIZE_MB", "5"))
        admin_token = os.getenv("ADMIN_TOKEN")
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_channel_id = os.getenv("TELEGRAM_CHANNEL_ID")

        if not supabase_url:
            raise RuntimeError("SUPABASE_URL is not set")

        if not supabase_key:
            raise RuntimeError(
                "SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY is not set"
            )

        if not access_key or not secret_key:
            raise RuntimeError("DigitalOcean Spaces credentials are not set")

        if not bucket:
            raise RuntimeError("DIGITALOCEAN_BUCKET_NAME is not set")

        if not region:
            raise RuntimeError("DIGITALOCEAN_REGION is not set")

        if not cdn_endpoint:
            raise RuntimeError("DIGITALOCEAN_CDN is not set")

        if not origin_endpoint:
            origin_endpoint = f"https://{bucket}.{region}.digitaloceanspaces.com"

        return cls(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            supabase_bucket=supabase_bucket,
            digitalocean_access_key=access_key,
            digitalocean_secret_key=secret_key,
            digitalocean_bucket=bucket,
            digitalocean_region=region,
            digitalocean_cdn_endpoint=cdn_endpoint.rstrip("/"),
            digitalocean_origin_endpoint=origin_endpoint.rstrip("/"),
            digitalocean_upload_prefix=normalized_prefix,
            digitalocean_max_file_size_mb=max_file_size_mb,
            admin_token=admin_token,
            telegram_bot_token=telegram_bot_token,
            telegram_channel_id=telegram_channel_id,
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings so we only parse env once."""
    return Settings.from_env()
