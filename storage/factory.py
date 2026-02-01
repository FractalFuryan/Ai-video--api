from config import settings
from storage.base import StorageBackend
from storage.local import LocalStorage
from storage.s3 import S3Storage


def get_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND.lower() == "s3":
        return S3Storage(
            bucket=settings.S3_BUCKET,
            region=settings.S3_REGION,
            endpoint_url=settings.AWS_ENDPOINT_URL,
        )
    return LocalStorage(settings.STORAGE_LOCAL_DIR)
