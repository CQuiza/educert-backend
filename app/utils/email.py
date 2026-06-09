"""Envío de correos electrónicos usando fastapi-mail."""

import logging
from datetime import datetime, timezone

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

from app.core.settings import get_settings
from app.models.enums import EmailStatus
from app.utils.email_templates import credentials_body, expired_body, issued_body

logger = logging.getLogger(__name__)

_mail_config: ConnectionConfig | None = None


def _get_mail_config() -> ConnectionConfig | None:
    global _mail_config
    if _mail_config is not None:
        return _mail_config
    settings = get_settings()
    if not settings.smtp_host:
        return None
    _mail_config = ConnectionConfig(
        MAIL_USERNAME=settings.smtp_user,
        MAIL_PASSWORD=settings.smtp_password,
        MAIL_FROM=settings.email_from,
        MAIL_PORT=settings.smtp_port,
        MAIL_SERVER=settings.smtp_host,
        MAIL_STARTTLS=settings.smtp_tls,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )
    return _mail_config


async def send_credentials_email(email_to: str, password: str) -> None:
    """Envía un correo con las credenciales al usuario recién creado."""
    conf = _get_mail_config()
    if conf is None:
        logger.warning("SMTP no configurado. No se envió correo de credenciales a %s", email_to)
        return

    settings = get_settings()
    app_name = settings.project_name
    login_url = f"{settings.base_url.rstrip('/')}/login"
    message = MessageSchema(
        subject=f"Tus credenciales de acceso — {app_name}",
        recipients=[email_to],
        body=credentials_body(app_name, email_to, password, login_url),
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    logger.info("Correo de credenciales enviado a %s", email_to)


async def send_certificate_issued_email(
    email_to: str,
    student_name: str,
    certificate_uid: str,
    base_url: str,
    api_prefix: str = "",
) -> None:
    """Envía un correo notificando la emisión de un certificado."""
    conf = _get_mail_config()
    if conf is None:
        logger.warning("SMTP no configurado. No se envió correo de certificado emitido a %s", email_to)
        return

    settings = get_settings()
    app_name = settings.project_name
    verify_link = f"{base_url.rstrip('/')}{api_prefix}/certificates/view/{certificate_uid}"
    message = MessageSchema(
        subject=f"Tu certificado ha sido emitido — {app_name}",
        recipients=[email_to],
        body=issued_body(app_name, student_name, verify_link),
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    logger.info("Correo de certificado emitido enviado a %s", email_to)


async def send_certificate_expired_email(
    email_to: str,
    student_name: str,
    certificate_uid: str,
    base_url: str | None = None,
) -> None:
    """Envía un correo notificando la expiración de un certificado."""
    conf = _get_mail_config()
    if conf is None:
        logger.warning("SMTP no configurado. No se envió correo de certificado expirado a %s", email_to)
        return

    settings = get_settings()
    app_name = settings.project_name

    message = MessageSchema(
        subject=f"Tu certificado ha expirado — {app_name}",
        recipients=[email_to],
        body=expired_body(app_name, student_name),
        subtype="html",
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    logger.info("Correo de certificado expirado enviado a %s", email_to)


# ── Wrappers con auditoría para BackgroundTasks ──────────────

from app.core.database import AsyncSessionLocal
from app.models.email_audit import EmailAudit


async def send_credentials_with_audit(
    email_to: str,
    password: str,
    user_name: str | None = None,
) -> None:
    """Envía credenciales y registra resultado en email_audit."""
    status = EmailStatus.failed.value
    error_text: str | None = None
    try:
        await send_credentials_email(email_to, password)
        status = EmailStatus.sent.value
    except Exception as e:
        error_text = str(e)
        logger.exception("Error en send_credentials_with_audit para %s", email_to)

    async with AsyncSessionLocal() as session:
        session.add(EmailAudit(
            user_name=user_name,
            email_to=email_to,
            email_type="credentials",
            status=status,
            error=error_text,
            sent_at=datetime.now(timezone.utc) if status == EmailStatus.sent.value else None,
        ))
        await session.commit()


async def send_issued_with_audit(
    email_to: str,
    student_name: str,
    certificate_uid: str,
    base_url: str,
    api_prefix: str,
    user_name: str | None = None,
) -> None:
    """Notifica emisión de certificado y registra resultado en email_audit."""
    status = EmailStatus.failed.value
    error_text: str | None = None
    try:
        await send_certificate_issued_email(
            email_to, student_name, certificate_uid, base_url, api_prefix
        )
        status = EmailStatus.sent.value
    except Exception as e:
        error_text = str(e)
        logger.exception("Error en send_issued_with_audit para %s", email_to)

    async with AsyncSessionLocal() as session:
        session.add(EmailAudit(
            user_name=user_name,
            email_to=email_to,
            email_type="certificate_issued",
            status=status,
            error=error_text,
            metadata_={"certificate_uid": certificate_uid},
            sent_at=datetime.now(timezone.utc) if status == EmailStatus.sent.value else None,
        ))
        await session.commit()


async def send_expired_with_audit(
    email_to: str,
    student_name: str,
    certificate_uid: str,
    user_name: str | None = None,
) -> None:
    """Notifica expiración de certificado y registra resultado en email_audit."""
    status = EmailStatus.failed.value
    error_text: str | None = None
    try:
        await send_certificate_expired_email(email_to, student_name, certificate_uid)
        status = EmailStatus.sent.value
    except Exception as e:
        error_text = str(e)
        logger.exception("Error en send_expired_with_audit para %s", email_to)

    async with AsyncSessionLocal() as session:
        session.add(EmailAudit(
            user_name=user_name,
            email_to=email_to,
            email_type="certificate_expired",
            status=status,
            error=error_text,
            metadata_={"certificate_uid": certificate_uid},
            sent_at=datetime.now(timezone.utc) if status == EmailStatus.sent.value else None,
        ))
        await session.commit()
