"""
Configuración principal para el uso de celery beat y la coordinacion de tareas en segundo plano y programadas
"""

import os

from celery import Celery
from celery.schedules import crontab

from app.core import settings
from app.core.settings import Settings, get_settings

settings = get_settings()
# 1. Instanciamos Celery
celery_app = Celery(
    "main_worker",
    broker=settings.rabbitmq_url,
    # Incluimos el archivo de las tareas para que Celery las reconozca
    include=["app.workers.tasks"],
)

# 2. Configuración del BEAT (El despertador)
celery_app.conf.beat_schedule = {
    "evaluar-certificados-cada-medianoche": {
        "task": "app.workers.tasks.check_expired_certificates",
        "schedule": crontab(hour=0, minute=0),
    },
    "hacer-backup-bd-cada-madrugada": {
        "task": "app.workers.tasks.backup_database_to_minio",
        "schedule": crontab(hour=1, minute=0),
    },
    "hacer-backup-bd-cada-madrugada": {
        "task": "app.workers.tasks.backup_database_to_minio",
        "schedule": crontab(hour=1, minute=0),  # Todos los días a las 01:00
    },
}

celery_app.conf.result_backend = "rpc://"
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]

celery_app.conf.timezone = "America/Bogota"
