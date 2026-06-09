-- ============================================================
-- Migración 006: agregar original_filename a lesson_tasks.
-- Aplicar: psql ... -f migrations/006_add_original_filename.sql
-- ============================================================

BEGIN;

ALTER TABLE lesson_tasks
    ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255);

COMMIT;
