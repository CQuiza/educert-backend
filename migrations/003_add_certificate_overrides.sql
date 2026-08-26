-- Overrides por certificado: si se llenan, se persisten en la fila y el PDF
-- los usa incluso tras regenerar/reactivar/renovar; NULL = usar el tipo.
BEGIN;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS hours INTEGER;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS validity_years INTEGER;
COMMIT;
