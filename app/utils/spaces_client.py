import boto3
from botocore.config import Config

from app.utils.settings import get_settings


def get_spaces_client():
    """Return a boto3 client configured for DigitalOcean Spaces."""
    settings = get_settings()
    return boto3.client(
        "s3",
        region_name=settings.digitalocean_region,
        endpoint_url=settings.digitalocean_origin_endpoint,
        aws_access_key_id=settings.digitalocean_access_key,
        aws_secret_access_key=settings.digitalocean_secret_key,
        config=Config(signature_version="s3v4"),
    )
