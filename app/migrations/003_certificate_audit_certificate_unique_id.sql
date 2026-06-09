-- ============================================================
-- Migración 003: certificate_audit.certificate_unique_id (UUID del certificado)
-- + trigger para rellenar automáticamente desde certificates al insertar/actualizar certificate_id
-- Aplicar: psql ... -f migrations/003_certificate_audit_certificate_unique_id.sql
-- ============================================================

BEGIN;

ALTER TABLE certificate_audit
    ADD COLUMN IF NOT EXISTS certificate_unique_id UUID;

UPDATE certificate_audit AS ca
SET certificate_unique_id = c.unique_id
FROM certificates AS c
WHERE ca.certificate_id IS NOT NULL
  AND c.id = ca.certificate_id
  AND ca.certificate_unique_id IS NULL;

CREATE OR REPLACE FUNCTION fn_certificate_audit_fill_certificate_unique_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.certificate_id IS NOT NULL THEN
        SELECT c.unique_id
        INTO NEW.certificate_unique_id
        FROM certificates AS c
        WHERE c.id = NEW.certificate_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_certificate_audit_fill_certificate_unique_id ON certificate_audit;

CREATE TRIGGER tr_certificate_audit_fill_certificate_unique_id
    BEFORE INSERT OR UPDATE OF certificate_id ON certificate_audit
    FOR EACH ROW
    EXECUTE FUNCTION fn_certificate_audit_fill_certificate_unique_id();

CREATE INDEX IF NOT EXISTS idx_certificate_audit_certificate_unique_id
    ON certificate_audit (certificate_unique_id);

COMMIT;
