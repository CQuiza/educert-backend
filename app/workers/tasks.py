"""
Ejecuta las tareas diarias de expiración de certificados y backups de base de datos.
"""

import anyio
import logging
import os
import subprocess
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncWorkerSessionLocal
from app.core.settings import get_settings
from app.models.certificate import Certificate
from app.models.certificate_audit import CertificateAudit
from app.models.email_audit import EmailAudit
from app.models.enums import CertificateStatus, CertificateAuditAction, EmailStatus, WorkerStatus
from app.repositories.user_repository import user_repository
from app.services.certificate_storage import CertificateStorageService
from app.utils.certificate_editor import apply_revoked_watermark_pdf
from app.utils.email import send_certificate_expired_email
from app.utils.worker_audit import log_worker_action

logger = logging.getLogger(__name__)

@shared_task(name="app.workers.tasks.check_expired_certificates")
def check_expired_certificates():
    """
    Revisa certificados expirados, aplica marca de agua y actualiza la BD.
    """
    anyio.run(_async_check_expired_certificates)


async def _async_check_expired_certificates():
    settings = get_settings()
    now = datetime.now(timezone.utc)
    started_at = now
    task_name = "check_expired_certificates"
    processed = 0
    errors = []

    async with AsyncWorkerSessionLocal() as session:
        await log_worker_action(
            session, task_name=task_name, status=WorkerStatus.running.value,
            started_at=started_at,
        )

        stmt = select(Certificate).options(
            selectinload(Certificate.user)
        ).where(
            Certificate.status == CertificateStatus.active.value,
            Certificate.expires_at <= now
        )
        result = await session.execute(stmt)
        certificates = result.scalars().all()

        if not certificates:
            await log_worker_action(
                session, task_name=task_name, status=WorkerStatus.success.value,
                started_at=started_at, finished_at=datetime.now(timezone.utc),
                details="No se encontraron certificados expirados",
            )
            await session.commit()
            return

        storage = CertificateStorageService(settings)
        system_user = await user_repository.get_by_email(session, settings.system_bot_user_email)
        system_bot_id = system_user.id if system_user else None

        for cert in certificates:
            uid_str = str(cert.unique_id)

            try:
                raw_pdf = await storage.download_pdf(uid_str)
                watermarked_pdf = apply_revoked_watermark_pdf(raw_pdf, watermark_text="EXPIRADO")
                await storage.upload_pdf(uid_str, watermarked_pdf)
            except Exception as e:
                errors.append(f"Certificado {cert.id}: {e}")
                continue

            cert.status = CertificateStatus.expired.value

            audit = CertificateAudit(
                certificate_id=cert.id,
                certificate_unique_id=cert.unique_id,
                action=CertificateAuditAction.expired.value,
                performed_by=system_bot_id,
            )
            session.add(audit)

            student_user = cert.user
            if student_user and student_user.email:
                email_audit = EmailAudit(
                    user_name=student_user.name,
                    email_to=student_user.email,
                    email_type="certificate_expired",
                )
                session.add(email_audit)
                await session.flush()
                try:
                    await send_certificate_expired_email(
                        email_to=student_user.email,
                        student_name=student_user.name or "Estudiante",
                        certificate_uid=uid_str,
                    )
                    email_audit.status = EmailStatus.sent.value
                    email_audit.sent_at = func.now()
                except Exception as e:
                    email_audit.status = EmailStatus.failed.value
                    email_audit.error = str(e)
                    logger.exception("Error enviando correo de expiración a %s", student_user.email)

            processed += 1

        await session.flush()

        details_parts = [f"{processed} certificados expirados"]
        if errors:
            details_parts.append(f"Errores: {'; '.join(errors)}")

        await log_worker_action(
            session, task_name=task_name, status=WorkerStatus.success.value,
            started_at=started_at, finished_at=datetime.now(timezone.utc),
            details=" | ".join(details_parts),
        )

        await session.commit()


@shared_task(name="app.workers.tasks.backup_database_to_minio")
def backup_database_to_minio():
    """
    Realiza un backup de la base de datos usando pg_dump y lo sube a MinIO.
    """
    anyio.run(_async_backup_database_to_minio)


async def _async_backup_database_to_minio():
    """Sube el dump diario al MinIO EXTERNO de backup (regla 3-2-1).

    Sin fallback interno: si el MinIO externo falla o no está configurado, el
    dump se envía ADJUNTO por correo como fallback real y la tarea queda
    `failed` en worker_audit.
    """
    from app.utils.email import send_backup_email_with_audit
    from app.utils.minio_client import get_backup_minio_client

    settings = get_settings()
    started_at = datetime.now(timezone.utc)
    task_name = "backup_database_to_minio"
    status = WorkerStatus.running.value
    details: str | None = None

    host = settings.postgres_host
    port = settings.postgres_port
    user = settings.postgres_user
    password = settings.postgres_password
    db = settings.postgres_db

    timestamp = started_at.strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{db}_{timestamp}.sql"
    filepath = f"/tmp/{filename}"

    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    cmd = [
        "pg_dump",
        "-h", str(host),
        "-p", str(port),
        "-U", str(user),
        "-d", str(db),
        "-F", "c",
        "-f", filepath,
    ]

    try:
        async with AsyncWorkerSessionLocal() as session:
            try:
                await log_worker_action(
                    session, task_name=task_name, status=WorkerStatus.running.value,
                    started_at=started_at,
                )
                await session.flush()

                logger.info("Iniciando pg_dump para backup %s", filename)
                subprocess.run(cmd, env=env, check=True, capture_output=True)
                logger.info("pg_dump completado para %s", filename)

                file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

                # Primario: MinIO externo de backup, sin fallback interno
                upload_error: str | None = None
                uploaded = False
                backup_client = get_backup_minio_client(settings)
                if backup_client is None:
                    upload_error = (
                        "MinIO de backup no configurado "
                        "(MINIO_BACKUP_ACCESS_KEY/MINIO_BACKUP_SECRET_KEY)"
                    )
                    logger.warning(upload_error)
                else:
                    try:
                        backup_client.ensure_bucket()
                        object_name = f"{settings.minio_backup_path_db.strip('/')}/{filename}"
                        backup_client.client.fput_object(
                            backup_client.bucket,
                            object_name,
                            filepath,
                            metadata={
                                "backup_created_at": started_at.isoformat(),
                                "backup_filename": filename,
                            },
                        )
                        uploaded = True
                        logger.info(
                            "Backup %s subido al MinIO externo (bucket=%s)",
                            filename, backup_client.bucket,
                        )
                    except Exception as e:
                        upload_error = f"Error subiendo al MinIO externo: {e}"
                        logger.exception(upload_error)

                # Notificación: sin adjunto si subió; con el dump adjunto si falló
                email_to = settings.backup_email_to or settings.superuser_email
                email_sent = False
                if email_to:
                    try:
                        email_sent = await send_backup_email_with_audit(
                            session,
                            email_to=email_to,
                            filename=filename,
                            size_bytes=file_size,
                            uploaded=uploaded,
                            attachment_path=None if uploaded else filepath,
                            extra=upload_error,
                        )
                    except Exception as e:
                        logger.exception("Error enviando correo de backup: %s", e)
                await session.flush()

                if uploaded:
                    status = WorkerStatus.success.value
                    details = (
                        f"Backup {filename} subido al MinIO externo ({file_size} bytes)"
                        + (f" | correo de notificación {'enviado' if email_sent else 'NO enviado'}"
                           if email_to else "")
                    )
                else:
                    status = WorkerStatus.failed.value
                    details = (
                        f"Error en backup: {upload_error}"
                        + (
                            " | correo de fallback enviado"
                            if email_sent
                            else " | correo de fallback NO enviado"
                        )
                        if email_to
                        else f"Error en backup: {upload_error}"
                    )
                logger.info(details)

            except subprocess.CalledProcessError as e:
                detail_str = e.stderr.decode("utf-8", errors="replace")
                status = WorkerStatus.failed.value
                details = f"pg_dump falló: {detail_str}"
                logger.error(details)

            await log_worker_action(
                session, task_name=task_name, status=status,
                started_at=started_at, finished_at=datetime.now(timezone.utc),
                details=details,
            )
            await session.commit()

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.debug("Archivo temporal %s eliminado", filepath)

    if status == WorkerStatus.failed.value:
        logger.error("Backup falló: %s", details)
