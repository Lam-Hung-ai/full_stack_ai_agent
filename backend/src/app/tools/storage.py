"""Object storage commands: `uv run storage setup`.

Creates the bucket if missing, allows the frontend origins to PUT and GET
with presigned URLs (bucket CORS, AGENTS §17.7) and expires abandoned
uploads under `private/temp/` after a day. Safe to run again.
"""

import argparse

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

TEMP_PREFIX = "private/temp/"
TEMP_DAYS = 1


def _setup() -> None:
    from app.config.settings import get_settings

    settings = get_settings()
    if not settings.storage_access_key_id or not settings.storage_secret_access_key:
        raise SystemExit(
            "STORAGE_ACCESS_KEY_ID and STORAGE_SECRET_ACCESS_KEY are not set"
        )
    client = boto3.client(
        "s3",
        endpoint_url=settings.storage_endpoint_url,
        aws_access_key_id=settings.storage_access_key_id,
        aws_secret_access_key=settings.storage_secret_access_key.get_secret_value(),
        region_name=settings.storage_region,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": settings.storage_addressing_style},
        ),
    )
    bucket = settings.storage_bucket
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError:
        client.create_bucket(Bucket=bucket)
        print(f"✓ Created bucket {bucket}")
    client.put_bucket_cors(
        Bucket=bucket,
        CORSConfiguration={
            "CORSRules": [
                {
                    "AllowedOrigins": settings.allowed_origins,
                    "AllowedMethods": ["PUT", "GET", "HEAD"],
                    "AllowedHeaders": ["Content-Type"],
                    "ExposeHeaders": ["ETag"],
                    "MaxAgeSeconds": 3600,
                }
            ]
        },
    )
    print(f"✓ CORS allows {', '.join(settings.allowed_origins)}")
    try:
        client.put_bucket_lifecycle_configuration(
            Bucket=bucket,
            LifecycleConfiguration={
                "Rules": [
                    {
                        "ID": "expire-abandoned-uploads",
                        "Filter": {"Prefix": TEMP_PREFIX},
                        "Status": "Enabled",
                        "Expiration": {"Days": TEMP_DAYS},
                    }
                ]
            },
        )
        print(f"✓ Objects under {TEMP_PREFIX} expire after {TEMP_DAYS} day")
    except ClientError as error:
        # Not every S3-compatible store implements lifecycle rules (RR-17).
        print(f"! Lifecycle rule not set: {error.response['Error'].get('Code')}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup"])
    parser.parse_args()
    _setup()


if __name__ == "__main__":
    main()
