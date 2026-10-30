from typing import Annotated

from fastapi import Depends

from app.common.exceptions.handlers import fail
from app.common.storage.client import ObjectStorage, get_object_storage
from app.common.storage.exceptions import StorageConfigurationError


def required_storage() -> ObjectStorage:
    try:
        return get_object_storage()
    except StorageConfigurationError:
        fail(503, "storage_unavailable")


def optional_storage() -> ObjectStorage | None:
    """For routes that need storage only when files are involved: a
    deployment without storage still chats, it just cannot attach files."""
    try:
        return get_object_storage()
    except StorageConfigurationError:
        return None


StorageDep = Annotated[ObjectStorage, Depends(required_storage)]
OptionalStorageDep = Annotated[ObjectStorage | None, Depends(optional_storage)]
