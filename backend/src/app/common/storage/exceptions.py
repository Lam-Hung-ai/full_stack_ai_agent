"""Storage boundary errors without leaking a concrete S3 SDK to domains."""


class ObjectStorageError(Exception):
    """The object store could not complete an operation."""


class ObjectNotFoundError(ObjectStorageError):
    """The requested object does not exist."""


class StorageConfigurationError(ObjectStorageError):
    """Object storage credentials or endpoints are not configured."""
