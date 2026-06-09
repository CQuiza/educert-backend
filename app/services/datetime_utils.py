"""Cálculo de caducidad de certificados."""

from datetime import UTC, datetime, timedelta


def compute_certificate_expires_at(
    issued_at: datetime,
    validity_type: str,
    validity_value: int,
) -> datetime:
    if issued_at.tzinfo is None:
        issued_at = issued_at.replace(tzinfo=UTC)
    vt = validity_type.lower().strip()
    if vt == "days":
        return issued_at + timedelta(days=validity_value)
    if vt == "months":
        return issued_at + timedelta(days=30 * validity_value)
    if vt == "years":
        return issued_at + timedelta(days=365 * validity_value)
    raise ValueError(f"Tipo de validez no soportado: {validity_type}")
