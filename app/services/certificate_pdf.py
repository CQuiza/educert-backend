"""Generación de PDF y QR de certificados, marcas de agua."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from pathlib import Path

from app.core.settings import Settings, get_settings
from app.models.certificate import Certificate
from app.models.certificate_type import CertificateType
from app.models.user import User
from app.utils.certificate_editor import (
    CertificateEditor,
    CertificateEditorData,
    apply_revoked_watermark_pdf,
)
from app.utils.helpers import student_display_name
from app.utils.make_qr_code import MakeQRCode

logger = logging.getLogger(__name__)

_APP_ROOT = Path(__file__).resolve().parent.parent


def _resolve_under_app(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else _APP_ROOT / p


def _issued_date(cert: Certificate) -> datetime:
    t = cert.issued_at
    if t is None:
        return datetime.now(UTC)
    if t.tzinfo is None:
        return t.replace(tzinfo=UTC)
    return t


class CertificatePdfService:
    """Genera PDF y QR de certificados. No sabe que MinIO existe."""

    def generate(
        self,
        student: User,
        certificate_type: CertificateType,
        issued_at: datetime,
        verify_url: str,
        settings: Settings,
        validity_years: int | None = None,
    ) -> tuple[bytes, bytes]:
        """Construye PDF + QR y devuelve (pdf_bytes, qr_bytes)."""
        logger.info("Generando PDF — student=%s, ct=%s", student.email, certificate_type.name)
        box = max(4, min(14, settings.qr_size // 20))
        qr_io = MakeQRCode(box_size=box).to_bytesio(verify_url)

        tpl = _resolve_under_app(settings.certificate_template_pdf)
        editor = CertificateEditor(tpl)
        overlay = CertificateEditorData(
            issued_on=issued_at.date(),
            student_full_name=student_display_name(student),
            identity_type=student.identity_type,
            identity_number=student.identity_number,
            certificate_type_kind=certificate_type.type,
            certificate_type_name=certificate_type.name,
            hours=certificate_type.hours,
            validity_years=validity_years,
        )
        pdf_io = editor.build_merged_pdf(overlay, qr_io)
        pdf_bytes = pdf_io.getvalue()
        qr_io.seek(0)
        qr_bytes = qr_io.read()
        logger.info("PDF generado — size=%s, qr_size=%s", len(pdf_bytes), len(qr_bytes))
        return pdf_bytes, qr_bytes

    async def regenerate(self, db, cert: Certificate) -> bytes:
        """Re-genera PDF (bytes) para un certificado existente."""
        logger.info("Regenerando PDF — uid=%s", str(cert.unique_id))
        from app.repositories.certificate_type_repository import (
            certificate_type_repository,
        )
        from app.repositories.user_repository import user_repository

        student = await user_repository.get_by_id(db, cert.user_id)
        ct = await certificate_type_repository.get_by_id(db, cert.certificate_type_id)
        if not student or not ct:
            logger.error("No se puede regenerar PDF — uid=%s: falta student o ct", str(cert.unique_id))
            msg = "No se puede regenerar el PDF: falta estudiante o tipo de certificado."
            raise ValueError(msg)

        settings = get_settings()
        issued_at = _issued_date(cert)
        uid = str(cert.unique_id)
        base = settings.base_url.rstrip("/")
        api = settings.api_v1_prefix.rstrip("/")
        verify_url = f"{base}{api}/certificates/view/{uid}"
        validity_years = ct.validity_value if ct.validity_type == "years" else None
        pdf_bytes, _ = self.generate(student, ct, issued_at, verify_url, settings, validity_years=validity_years)
        logger.info("PDF regenerado — uid=%s, size=%s", str(cert.unique_id), len(pdf_bytes))
        return pdf_bytes

    @staticmethod
    def apply_watermark(pdf_bytes: bytes, text: str) -> bytes:
        """Aplica texto de marca de agua a un PDF en bytes."""
        return apply_revoked_watermark_pdf(pdf_bytes, watermark_text=text)
