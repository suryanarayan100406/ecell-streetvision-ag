"""MinIO object storage client wrapper."""

from __future__ import annotations

from io import BytesIO
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

from app.config import settings

_client: Minio | None = None


def get_minio_client() -> Minio:
    """Get or create the MinIO client singleton."""
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE,
        )
        # Ensure bucket exists
        if not _client.bucket_exists(settings.MINIO_BUCKET):
            _client.make_bucket(settings.MINIO_BUCKET)
    return _client


def upload_file(object_name: str, data: BinaryIO | bytes, content_type: str = "application/octet-stream") -> str:
    """Upload a file to MinIO and return the object path."""
    client = get_minio_client()
    if isinstance(data, bytes):
        data_stream = BytesIO(data)
        length = len(data)
    else:
        data.seek(0, 2)
        length = data.tell()
        data.seek(0)
        data_stream = data

    client.put_object(
        settings.MINIO_BUCKET,
        object_name,
        data_stream,
        length=length,
        content_type=content_type,
    )
    return f"{settings.MINIO_BUCKET}/{object_name}"


def download_file(object_name: str) -> bytes:
    """Download a file from MinIO and return bytes."""
    client = get_minio_client()
    response = client.get_object(settings.MINIO_BUCKET, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def get_presigned_url(object_name: str, expires_hours: int = 1) -> str:
    """Generate a presigned URL for direct download."""
    from datetime import timedelta
    client = get_minio_client()
    return client.presigned_get_object(
        settings.MINIO_BUCKET,
        object_name,
        expires=timedelta(hours=expires_hours),
    )


def delete_file(object_name: str) -> None:
    """Delete a file from MinIO."""
    client = get_minio_client()
    client.remove_object(settings.MINIO_BUCKET, object_name)
