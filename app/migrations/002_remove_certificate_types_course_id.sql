-- ============================================================
-- Migración 002: quitar course_id de certificate_types (FK solo en courses)
-- y permitir borrar certificados conservando filas de auditoría.
-- Aplicar: psql ... -f migrations/002_remove_certificate_types_course_id.sql
-- ============================================================

BEGIN;

-- Necesario para DELETE de certificates cuando ya hay (o habrá) filas en certificate_audit
ALTER TABLE certificate_audit
    DROP CONSTRAINT IF EXISTS certificate_audit_certificate_id_fkey;

ALTER TABLE certificate_audit
    ADD CONSTRAINT certificate_audit_certificate_id_fkey
    FOREIGN KEY (certificate_id)
    REFERENCES certificates(id)
    ON DELETE SET NULL;

ALTER TABLE certificate_types
    DROP COLUMN IF EXISTS course_id;

COMMIT;
