"""Configuración de la aplicación con pydantic-settings."""

from email.policy import default
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de entorno tipadas."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base de datos
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    postgres_user: str | None = Field(default=None, alias="POSTGRES_USER")
    postgres_password: str | None = Field(default=None, alias="POSTGRES_PASSWORD")
    postgres_db: str | None = Field(default=None, alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")

    # JWT / OAuth2
    secret_key: str = Field(alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Contraseñas
    bcrypt_rounds: int = Field(default=12, alias="BCRYPT_ROUNDS")

    # Archivos / URLs públicas
    storage_path: str = Field(default="./storage", alias="STORAGE_PATH")
    base_url: str = Field(default="http://localhost:8000", alias="BASE_URL")
    qr_size: int = Field(default=200, alias="QR_SIZE")
    pdf_template_path: str = Field(
        default="./templates/certificate.html", alias="PDF_TEMPLATE_PATH"
    )
    certificate_template_pdf: str = Field(
        default="templates/certificate_template.pdf",
        alias="CERTIFICATE_TEMPLATE_PDF",
    )
    certificate_reference_pdf: str = Field(
        default="templates/certificate_reference.pdf",
        alias="CERTIFICATE_REFERENCE_PDF",
    )
    certificate_revoked_watermark_text: str = Field(
        default="REVOCADO",
        alias="CERTIFICATE_REVOKED_WATERMARK_TEXT",
    )

    # Email (opcional)
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int | None = Field(default=None, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_tls: bool = Field(default=True, alias="SMTP_TLS")
    email_from: str | None = Field(default=None, alias="EMAIL_FROM")

    check_expired_interval_hours: int = Field(
        default=24, alias="CHECK_EXPIRED_INTERVAL_HOURS"
    )

    # MinIO (p. ej. API local vía túnel SSH hacia la VPS)
    minio_endpoint: str = Field(default="127.0.0.1:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str | None = Field(default=None, alias="MINIO_ACCESS_KEY")
    minio_secret_key: str | None = Field(default=None, alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="certify", alias="MINIO_BUCKET")
    minio_path_pdf: str = Field(default="certifications/pdf", alias="MINIO_PATH_PDF")
    minio_path_qr: str = Field(default="certifications/qr", alias="MINIO_PATH_QR")
    minio_path_backup_db: str = Field(
        default="backup/database", alias="MINIO_PATH_BACKUP_DB"
    )
    minio_path_backup_cert: str = Field(
        default="backup/certificates", alias="MINIO_PATH_BACKUP_CERT"
    )
    minio_path_tasks: str = Field(
        default="tasks/files", alias="MINIO_PATH_TASKS"
    )
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")
    minio_region: str = Field(default="", alias="MINIO_REGION")

    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        alias="ENVIRONMENT",
    )
    debug: bool = Field(default=False, alias="DEBUG")

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"], alias="ALLOWED_HOSTS")

    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    project_name: str = Field(default="Certify API", alias="PROJECT_NAME")

    # Superusuario inicial (seed)
    superuser_email: str = Field(default="admin@certify.local", alias="SUPERUSER_EMAIL")
    superuser_password: str = Field(default="Ch4ng3M3!", alias="SUPERUSER_PASSWORD")
    superuser_name: str = Field(default="Admin", alias="SUPERUSER_NAME")
    superuser_first_last_name: str = Field(
        default="Certify", alias="SUPERUSER_FIRST_LAST_NAME"
    )
    superuser_identity_type: str = Field(default="CC", alias="SUPERUSER_IDENTITY_TYPE")
    superuser_identity_number: str = Field(
        default="0000000000", alias="SUPERUSER_IDENTITY_NUMBER"
    )
    superuser_phone_number: str = Field(
        default="+570000000000", alias="SUPERUSER_PHONE_NUMBER"
    )

    system_bot_user_email: str = Field(
        default="system@certify.com", alias="SYSTEM_BOT_USER_EMAIL"
    )
    system_bot_user_name: str = Field(
        default="System", alias="SYSTEM_BOT_USER_NAME"
    )
    system_bot_user_first_last_name: str = Field(
        default="Bot", alias="SYSTEM_BOT_USER_FIRST_LAST_NAME"
    )

    task_max_upload_size_mb: int = Field(
        default=50, alias="TASK_MAX_UPLOAD_SIZE_MB"
    )

    rabbitmq_url: str = Field(
        default="amqp://user:pass@host:5672//", alias="RABBITMQ_URL"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: object) -> object:
        if v is None or v == "":
            return ["http://localhost:3000"]
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                import json

                return json.loads(s)
            return [p.strip() for p in s.split(",") if p.strip()]
        return v

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: object) -> object:
        if v is None or v == "":
            return ["localhost", "127.0.0.1"]
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                import json

                return json.loads(s)
            return [p.strip() for p in s.split(",") if p.strip()]
        return v

    def get_database_url(self) -> str:
        """URL de conexión (postgresql://...) construida o explícita."""
        if self.database_url:
            return self.database_url
        if (
            self.postgres_user
            and self.postgres_password is not None
            and self.postgres_db
        ):
            return (
                f"postgresql://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        raise ValueError(
            "Defina DATABASE_URL o POSTGRES_USER, POSTGRES_PASSWORD y POSTGRES_DB",
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
