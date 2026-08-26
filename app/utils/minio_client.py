"""Cliente MinIO: conexión (p. ej. localhost con túnel SSH) y subida/bajada de PDF y QR."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

logger = logging.getLogger(__name__)

from minio import Minio

from app.core.settings import Settings, get_settings

_DEFAULT_REGION = ""


def _normalize_minio_endpoint(endpoint: str) -> str:
    """El SDK espera ``host`` o ``host:puerto``, sin esquema."""
    e = endpoint.strip()
    if e.startswith("https://"):
        e = e[8:]
    elif e.startswith("http://"):
        e = e[7:]
    return e.rstrip("/")


class MinioClient:
    """Encapsula el SDK `minio` para el bucket configurado en settings."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket: str | None = None,
        secure: bool | None = None,
        region: str | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._endpoint_override = endpoint
        self._access_key_override = access_key
        self._secret_key_override = secret_key
        self._bucket_override = bucket
        self._secure_override = secure
        self._region_override = region
        self._client: Minio | None = None

    @property
    def bucket(self) -> str:
        if self._bucket_override is not None:
            return self._bucket_override
        return self._settings.minio_bucket

    @property
    def client(self) -> Minio:
        if self._client is None:
            s = self._settings
            access_key = self._access_key_override
            secret_key = self._secret_key_override
            if access_key is None or secret_key is None:
                access_key = s.minio_access_key
                secret_key = s.minio_secret_key
            if not access_key or not secret_key:
                msg = "Defina MINIO_ACCESS_KEY y MINIO_SECRET_KEY para usar MinIO"
                raise ValueError(msg)
            region = self._region_override
            if region is None:
                region = s.minio_region or _DEFAULT_REGION
            secure = self._secure_override
            if secure is None:
                secure = s.minio_secure
            endpoint = self._endpoint_override
            if endpoint is None:
                endpoint = s.minio_endpoint
            self._client = Minio(
                _normalize_minio_endpoint(endpoint),
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
                region=region,
            )
        return self._client

    def ensure_bucket(self) -> None:
        """Crea el bucket si no existe (idempotente)."""
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def download_bytes(self, object_name: str) -> bytes:
        """Descarga el objeto completo en memoria."""
        r = self.client.get_object(self.bucket, object_name)
        try:
            return r.read()
        finally:
            r.close()
            r.release_conn()

    def upload_bytes(
        self,
        object_name: str,
        data: bytes,
        *,
        content_type: str,
    ) -> None:
        """Sube bytes en memoria (p. ej. QR o PDF generados al vuelo)."""
        stream: BinaryIO = BytesIO(data)
        self.client.put_object(
            self.bucket,
            object_name,
            stream,
            length=len(data),
            content_type=content_type,
        )

    def remove_object(self, object_name: str) -> None:
        """Elimina un objeto del bucket. No falla si el objeto no existe."""
        from minio.error import S3Error
        try:
            self.client.remove_object(self.bucket, object_name)
        except S3Error as e:
            if e.code not in ("NoSuchKey", "NotFound"):
                logger.warning("Error al eliminar %s/%s: %s", self.bucket, object_name, e)
        except Exception as e:
            logger.error("Error inesperado al eliminar %s/%s: %s", self.bucket, object_name, e)


def get_minio_client(settings: Settings | None = None) -> MinioClient:
    return MinioClient(settings=settings)


def get_backup_minio_client(settings: Settings | None = None) -> MinioClient | None:
    """Cliente para el MinIO EXTERNO de backups; None si no está configurado."""
    s = settings or get_settings()
    if not s.minio_backup_access_key or not s.minio_backup_secret_key:
        return None
    return MinioClient(
        s,
        endpoint=s.minio_backup_endpoint,
        access_key=s.minio_backup_access_key,
        secret_key=s.minio_backup_secret_key,
        bucket=s.minio_backup_bucket,
        secure=s.minio_backup_secure,
        region=s.minio_backup_region,
    )
