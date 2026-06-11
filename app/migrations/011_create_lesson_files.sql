-- ============================================================
-- Migración 011: tabla lesson_files para archivos de lecciones.
-- Aplicar: psql ... -f migrations/011_create_lesson_files.sql
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS lesson_files (
    id                INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    lesson_id         INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    original_filename VARCHAR(255),
    mime_type         VARCHAR(100),
    file_url          TEXT,
    order_index       INTEGER NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lesson_files_lesson_id
    ON lesson_files (lesson_id);

CREATE INDEX IF NOT EXISTS idx_lesson_files_order
    ON lesson_files (lesson_id, order_index);

COMMIT;
