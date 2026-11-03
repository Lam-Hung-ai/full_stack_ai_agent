"""Object storage commands: `uv run storage setup|cleanup`.

`setup` creates the bucket if missing, allows the frontend origins to PUT and
GET with presigned URLs (bucket CORS, AGENTS §17.7) and expires abandoned
uploads under `private/temp/` after a day. `cleanup` deletes files never
attached to a question and the bytes of copies that will never finish
(RR-17, RR-18); run it daily. Both are safe to run again.
"""

import argparse
import asyncio
from datetime import timedelta

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

TEMP_PREFIX = "private/temp/"
TEMP_DAYS = 1
#: How long a file may wait for its question, or a copy for its next attempt.
CLEANUP_AFTER = timedelta(days=1)


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


async def _cleanup() -> None:
    from app.common.storage.client import get_object_storage
    from app.database.session import SessionLocal, engine
    from app.modules.files.cleanup import purge_unattached
    from app.modules.shares.copies import purge_abandoned_copies

    storage = get_object_storage()
    try:
        files = await purge_unattached(
            session_factory=SessionLocal, storage=storage, older_than=CLEANUP_AFTER
        )
        print(f"✓ Removed {files} unattached file(s)")
        copies = await purge_abandoned_copies(
            session_factory=SessionLocal, storage=storage, older_than=CLEANUP_AFTER
        )
        print(f"✓ Purged {copies} cancelled copy job(s)")
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup", "cleanup"])
    if parser.parse_args().command == "cleanup":
        asyncio.run(_cleanup())
    else:
        _setup()


if __name__ == "__main__":
    main()
