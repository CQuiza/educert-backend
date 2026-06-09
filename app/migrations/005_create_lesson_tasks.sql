-- ============================================================
-- Migración 005: tabla lesson_tasks para tareas de lecciones.
-- Aplicar: psql ... -f migrations/005_create_lesson_tasks.sql
-- ============================================================

BEGIN;

-- Crear tabla de tareas
CREATE TABLE IF NOT EXISTS lesson_tasks (
    id                INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    lesson_id         INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    title             VARCHAR(255) NOT NULL,
    description       TEXT,
    file_type         VARCHAR(20) NOT NULL DEFAULT 'none',
    file_url          TEXT,
    google_drive_link TEXT,
    order_index       INTEGER NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_lesson_tasks_lesson_id
    ON lesson_tasks (lesson_id);

CREATE INDEX IF NOT EXISTS idx_lesson_tasks_order
    ON lesson_tasks (lesson_id, order_index);

-- CHECK: file_type
ALTER TABLE lesson_tasks
    ADD CONSTRAINT ck_lesson_tasks_file_type
    CHECK (file_type IN ('none', 'upload', 'google_drive'));

COMMIT;
