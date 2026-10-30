"""An in-memory ObjectStorage (AGENTS §17.8: tests never call RustFS)."""

import pytest

from app.common.storage.exceptions import ObjectNotFoundError
from app.common.storage.schemas import ObjectHead, PresignedRequest


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], tuple[bytes, str]] = {}
        self.signed: list[PresignedRequest] = []

    def put(self, url: str, body: bytes, content_type: str) -> None:
        """What the browser's PUT to a presigned URL does."""
        bucket, key = url.removeprefix("http://storage.test/").split("/", 1)
        self.objects[(bucket, key)] = (body, content_type)

    def keys(self) -> set[str]:
        return {key for _, key in self.objects}

    def create_upload_request(self, *, bucket, object_key, content_type):
        request = PresignedRequest(
            url=f"http://storage.test/{bucket}/{object_key}",
            method="PUT",
            expires_in=600,
            headers={"Content-Type": content_type},
        )
        self.signed.append(request)
        return request

    def create_download_request(
        self, *, bucket, object_key, filename=None, inline=False
    ):
        disposition = "inline" if inline else "attachment"
        return PresignedRequest(
            url=f"http://storage.test/{bucket}/{object_key}?{disposition}",
            method="GET",
            expires_in=600,
        )

    async def head_object(self, *, bucket, object_key):
        body, content_type = self._get(bucket, object_key)
        return ObjectHead(len(body), content_type, None, None)

    async def read_object(self, *, bucket, object_key, max_bytes):
        return self._get(bucket, object_key)[0][: max_bytes + 1]

    async def read_prefix(self, *, bucket, object_key, length):
        return self._get(bucket, object_key)[0][:length]

    async def copy_object(
        self, *, source_bucket, source_key, destination_bucket, destination_key
    ):
        self.objects[(destination_bucket, destination_key)] = self._get(
            source_bucket, source_key
        )

    async def put_object(self, *, bucket, object_key, content_type, body):
        self.objects[(bucket, object_key)] = (body, content_type)

    async def delete_object(self, *, bucket, object_key):
        self.objects.pop((bucket, object_key), None)

    def _get(self, bucket, key):
        try:
            return self.objects[(bucket, key)]
        except KeyError:
            raise ObjectNotFoundError(key) from None


@pytest.fixture
def storage(client):
    from app.common.dependencies.storage import optional_storage, required_storage
    from app.main import app

    fake = FakeStorage()
    app.dependency_overrides[required_storage] = lambda: fake
    app.dependency_overrides[optional_storage] = lambda: fake
    yield fake
    app.dependency_overrides.pop(required_storage, None)
    app.dependency_overrides.pop(optional_storage, None)
