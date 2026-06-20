-- ============================================================
-- Migración 013: tabla task_submissions para entregas de tareas.
-- No modifica tablas existentes. Solo crea task_submissions.
-- Aplicar: psql ... -f migrations/013_create_task_submissions.sql
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS task_submissions (
    id                INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    task_id           INTEGER NOT NULL REFERENCES lesson_tasks(id) ON DELETE CASCADE,
    user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_url          TEXT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    mime_type         VARCHAR(127) NOT NULL DEFAULT 'application/pdf',
    submitted_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(task_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_ts_task
    ON task_submissions (task_id);

CREATE INDEX IF NOT EXISTS idx_ts_user
    ON task_submissions (user_id);

COMMIT;
