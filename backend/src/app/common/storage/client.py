"""S3-compatible adapter used for RustFS and other S3 implementations.

Taken from hr-ai (QD-14). Domains depend on `ObjectStorage`, never on boto3;
synchronous SDK calls run in the threadpool.
"""

from collections.abc import Mapping
from functools import lru_cache
from typing import Protocol, cast
from urllib.parse import quote

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from starlette.concurrency import run_in_threadpool

from app.common.storage.exceptions import (
    ObjectNotFoundError,
    ObjectStorageError,
    StorageConfigurationError,
)
from app.common.storage.schemas import ObjectHead, PresignedRequest
from app.config.settings import Settings, get_settings


class ObjectStorage(Protocol):
    def create_upload_request(
        self, *, bucket: str, object_key: str, content_type: str
    ) -> PresignedRequest: ...

    def create_download_request(
        self,
        *,
        bucket: str,
        object_key: str,
        filename: str | None = None,
        inline: bool = False,
    ) -> PresignedRequest: ...

    async def head_object(self, *, bucket: str, object_key: str) -> ObjectHead: ...

    async def read_object(
        self, *, bucket: str, object_key: str, max_bytes: int
    ) -> bytes: ...

    async def read_prefix(
        self, *, bucket: str, object_key: str, length: int
    ) -> bytes: ...

    async def copy_object(
        self,
        *,
        source_bucket: str,
        source_key: str,
        destination_bucket: str,
        destination_key: str,
    ) -> None: ...

    async def put_object(
        self, *, bucket: str, object_key: str, content_type: str, body: bytes
    ) -> None: ...

    async def delete_object(self, *, bucket: str, object_key: str) -> None: ...


class _S3Client(Protocol):
    def generate_presigned_url(
        self,
        ClientMethod: str,
        Params: Mapping[str, object],
        ExpiresIn: int,
        HttpMethod: str | None = None,
    ) -> str: ...

    def head_object(self, **kwargs: object) -> Mapping[str, object]: ...

    def get_object(self, **kwargs: object) -> Mapping[str, object]: ...

    def copy_object(self, **kwargs: object) -> object: ...

    def put_object(self, **kwargs: object) -> object: ...

    def delete_object(self, **kwargs: object) -> object: ...


class _ReadableBody(Protocol):
    def read(self, amount: int | None = None) -> bytes: ...

    def close(self) -> None: ...


class Boto3ObjectStorage:
    def __init__(
        self,
        *,
        client: _S3Client,
        presign_client: _S3Client,
        presign_ttl_seconds: int,
    ) -> None:
        self._client = client
        self._presign_client = presign_client
        self._presign_ttl_seconds = presign_ttl_seconds

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "Boto3ObjectStorage":
        resolved = settings or get_settings()
        if not resolved.storage_access_key_id or not resolved.storage_secret_access_key:
            raise StorageConfigurationError(
                "object storage credentials are not configured"
            )

        config = Config(
            signature_version="s3v4",
            connect_timeout=5,
            read_timeout=15,
            retries={"max_attempts": 3, "mode": "standard"},
            s3={"addressing_style": resolved.storage_addressing_style},
        )
        credentials = {
            "aws_access_key_id": resolved.storage_access_key_id,
            "aws_secret_access_key": (
                resolved.storage_secret_access_key.get_secret_value()
            ),
            "region_name": resolved.storage_region,
            "config": config,
        }
        client = boto3.client(
            "s3", endpoint_url=resolved.storage_endpoint_url, **credentials
        )
        if resolved.storage_presign_endpoint_url == resolved.storage_endpoint_url:
            presign_client = client
        else:
            presign_client = boto3.client(
                "s3",
                endpoint_url=resolved.storage_presign_endpoint_url,
                **credentials,
            )
        return cls(
            client=cast(_S3Client, client),
            presign_client=cast(_S3Client, presign_client),
            presign_ttl_seconds=resolved.storage_presign_ttl_seconds,
        )

    def create_upload_request(
        self, *, bucket: str, object_key: str, content_type: str
    ) -> PresignedRequest:
        params: dict[str, object] = {
            "Bucket": bucket,
            "Key": object_key,
            "ContentType": content_type,
        }
        try:
            url = self._presign_client.generate_presigned_url(
                "put_object",
                Params=params,
                ExpiresIn=self._presign_ttl_seconds,
                HttpMethod="PUT",
            )
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageError("could not create upload URL") from exc
        return PresignedRequest(
            url=url,
            method="PUT",
            expires_in=self._presign_ttl_seconds,
            headers={"Content-Type": content_type},
        )

    def create_download_request(
        self,
        *,
        bucket: str,
        object_key: str,
        filename: str | None = None,
        inline: bool = False,
    ) -> PresignedRequest:
        # `inline` opens the file in the tab instead of downloading it. Callers
        # enable it only for safe content types: opening an uploaded file
        # inline runs its content on the object store's origin.
        params: dict[str, object] = {"Bucket": bucket, "Key": object_key}
        if filename:
            encoded = quote(filename.replace("\r", "").replace("\n", ""), safe="")
            disposition = "inline" if inline else "attachment"
            params["ResponseContentDisposition"] = (
                f"{disposition}; filename*=UTF-8''{encoded}"
            )
        try:
            url = self._presign_client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=self._presign_ttl_seconds,
                HttpMethod="GET",
            )
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageError("could not create download URL") from exc
        return PresignedRequest(
            url=url,
            method="GET",
            expires_in=self._presign_ttl_seconds,
        )

    async def head_object(self, *, bucket: str, object_key: str) -> ObjectHead:
        try:
            response = await run_in_threadpool(
                self._client.head_object,
                Bucket=bucket,
                Key=object_key,
            )
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchKey", "NotFound"}:
                raise ObjectNotFoundError("object does not exist") from exc
            raise ObjectStorageError("could not inspect object") from exc
        except BotoCoreError as exc:
            raise ObjectStorageError("could not inspect object") from exc

        return ObjectHead(
            size_bytes=_non_negative_integer(response.get("ContentLength")),
            content_type=_optional_string(response.get("ContentType")),
            etag=_optional_string(response.get("ETag")),
            checksum_sha256=_optional_string(response.get("ChecksumSHA256")),
        )

    async def read_object(
        self, *, bucket: str, object_key: str, max_bytes: int
    ) -> bytes:
        def read() -> bytes:
            response = self._client.get_object(Bucket=bucket, Key=object_key)
            body = cast(_ReadableBody | None, response.get("Body"))
            if body is None:
                raise ObjectStorageError("object store returned no response body")
            try:
                content = body.read(max_bytes + 1)
            finally:
                body.close()
            if len(content) > max_bytes:
                raise ObjectStorageError("object exceeds the allowed size")
            return content

        try:
            return await run_in_threadpool(read)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchKey", "NotFound"}:
                raise ObjectNotFoundError("object does not exist") from exc
            raise ObjectStorageError("could not read object") from exc
        except BotoCoreError as exc:
            raise ObjectStorageError("could not read object") from exc

    async def read_prefix(self, *, bucket: str, object_key: str, length: int) -> bytes:
        """The first bytes of an object over an HTTP Range, to sniff its real
        format without pulling a large object into memory (AGENTS §17.6)."""

        def read() -> bytes:
            response = self._client.get_object(
                Bucket=bucket,
                Key=object_key,
                Range=f"bytes=0-{length - 1}",
            )
            body = cast(_ReadableBody | None, response.get("Body"))
            if body is None:
                raise ObjectStorageError("object store returned no response body")
            try:
                return body.read(length)
            finally:
                body.close()

        try:
            return await run_in_threadpool(read)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchKey", "NotFound"}:
                raise ObjectNotFoundError("object does not exist") from exc
            raise ObjectStorageError("could not read object") from exc
        except BotoCoreError as exc:
            raise ObjectStorageError("could not read object") from exc

    async def copy_object(
        self,
        *,
        source_bucket: str,
        source_key: str,
        destination_bucket: str,
        destination_key: str,
    ) -> None:
        try:
            await run_in_threadpool(
                self._client.copy_object,
                Bucket=destination_bucket,
                Key=destination_key,
                CopySource={"Bucket": source_bucket, "Key": source_key},
                MetadataDirective="COPY",
            )
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageError("could not copy object") from exc

    async def put_object(
        self, *, bucket: str, object_key: str, content_type: str, body: bytes
    ) -> None:
        """Backend-side write, for when the backend must be the writer; the
        normal upload is a presigned PUT straight from the browser."""
        try:
            await run_in_threadpool(
                self._client.put_object,
                Bucket=bucket,
                Key=object_key,
                ContentType=content_type,
                Body=body,
            )
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageError("could not store object") from exc

    async def delete_object(self, *, bucket: str, object_key: str) -> None:
        try:
            await run_in_threadpool(
                self._client.delete_object,
                Bucket=bucket,
                Key=object_key,
            )
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageError("could not delete object") from exc


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _non_negative_integer(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    raise ObjectStorageError("object store returned an invalid content length")


@lru_cache(maxsize=1)
def get_object_storage() -> ObjectStorage:
    """One adapter per process: boto3 clients are thread-safe and costly to build."""
    return Boto3ObjectStorage.from_settings()
