"""Subida, descarga y borrado de archivos de certificados en MinIO."""

from __future__ import annotations

import asyncio
import logging

from app.core.settings import Settings, get_settings
from app.utils.minio_client import get_minio_client

logger = logging.getLogger(__name__)


class CertificateStorageService:
    """Encapsula todas las operaciones de almacenamiento de certificados en MinIO.

    Responsabilidades:
    - Subir PDF + QR al emitir un certificado
    - Descargar PDF (para aplicar marcas de agua)
    - Subir PDF reemplazado (tras marca de agua)
    - Eliminar PDF + QR al borrar un certificado

    Las claves de objeto se derivan de ``settings.minio_path_pdf`` y
    ``settings.minio_path_qr``.
    """

    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        if not (self._settings.minio_access_key and self._settings.minio_secret_key):
            msg = "MinIO es obligatorio: defina MINIO_ACCESS_KEY y MINIO_SECRET_KEY."
            raise RuntimeError(msg)

    # ── helpers de clave ──────────────────────────────────────

    def _pdf_key(self, uid: str) -> str:
        prefix = self._settings.minio_path_pdf.strip("/")
        return f"{prefix}/{uid}.pdf" if prefix else f"{uid}.pdf"

    def _qr_key(self, uid: str) -> str:
        prefix = self._settings.minio_path_qr.strip("/")
        return f"{prefix}/{uid}.png" if prefix else f"{uid}.png"

    # ── upload ────────────────────────────────────────────────

    async def upload_certificate_files(
        self, uid: str, pdf_bytes: bytes, qr_bytes: bytes
    ) -> None:
        """Sube PDF y QR al bucket."""
        logger.info("Subiendo PDF+QR a MinIO — uid=%s", uid)

        def go() -> None:
            mc = get_minio_client(self._settings)
            mc.ensure_bucket()
            mc.upload_bytes(self._pdf_key(uid), pdf_bytes, content_type="application/pdf")
            mc.upload_bytes(self._qr_key(uid), qr_bytes, content_type="image/png")

        try:
            await asyncio.to_thread(go)
            logger.info("PDF+QR subidos — uid=%s", uid)
        except Exception as exc:
            logger.exception("Error subiendo PDF+QR a MinIO — uid=%s", uid)
            msg = "No se pudo subir el PDF o el QR a MinIO (endpoint, credenciales o red)."
            raise RuntimeError(msg) from exc

    async def upload_pdf(self, uid: str, pdf_bytes: bytes) -> None:
        """Sube solo el PDF (útil tras regenerar o marcar con agua)."""
        logger.info("Subiendo PDF a MinIO — uid=%s", uid)

        def go() -> None:
            mc = get_minio_client(self._settings)
            mc.ensure_bucket()
            mc.upload_bytes(self._pdf_key(uid), pdf_bytes, content_type="application/pdf")

        try:
            await asyncio.to_thread(go)
            logger.info("PDF subido — uid=%s", uid)
        except Exception as exc:
            logger.exception("Error subiendo PDF a MinIO — uid=%s", uid)
            msg = "No se pudo subir el PDF a MinIO."
            raise RuntimeError(msg) from exc

    # ── download ──────────────────────────────────────────────

    async def download_pdf(self, uid: str) -> bytes:
        """Descarga el PDF del bucket."""
        logger.info("Descargando PDF de MinIO — uid=%s", uid)

        def go() -> bytes:
            mc = get_minio_client(self._settings)
            return mc.download_bytes(self._pdf_key(uid))

        try:
            data = await asyncio.to_thread(go)
            logger.info("PDF descargado — uid=%s, size=%s", uid, len(data))
            return data
        except Exception as exc:
            logger.exception("Error descargando PDF de MinIO — uid=%s", uid)
            msg = "No se pudo descargar el PDF de MinIO."
            raise RuntimeError(msg) from exc

    # ── delete ────────────────────────────────────────────────

    async def delete_certificate_files(self, uid: str) -> None:
        """Elimina PDF y QR del bucket."""
        logger.info("Eliminando PDF+QR de MinIO — uid=%s", uid)

        def go() -> None:
            mc = get_minio_client(self._settings)
            mc.remove_object(self._pdf_key(uid))
            mc.remove_object(self._qr_key(uid))

        try:
            await asyncio.to_thread(go)
            logger.info("PDF+QR eliminados — uid=%s", uid)
        except Exception as exc:
            logger.exception("Error eliminando archivos de MinIO — uid=%s", uid)
            msg = "No se pudieron eliminar los archivos del certificado en MinIO."
            raise RuntimeError(msg) from exc
