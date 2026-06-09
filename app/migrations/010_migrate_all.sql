-- ============================================================
-- Migración 005: tabla lesson_tasks
-- ============================================================

BEGIN;

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

CREATE INDEX IF NOT EXISTS idx_lesson_tasks_lesson_id
    ON lesson_tasks (lesson_id);

CREATE INDEX IF NOT EXISTS idx_lesson_tasks_order
    ON lesson_tasks (lesson_id, order_index);

ALTER TABLE lesson_tasks
    ADD CONSTRAINT ck_lesson_tasks_file_type
    CHECK (file_type IN ('none', 'upload', 'google_drive'));

COMMIT;

-- ============================================================
-- Migración 006: original_filename en lesson_tasks
-- ============================================================

BEGIN;

ALTER TABLE lesson_tasks
    ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255);

COMMIT;

-- ============================================================
-- Migración 007: tabla user_audit
-- ============================================================

CREATE TABLE IF NOT EXISTS user_audit (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    deleted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    snapshot JSONB NOT NULL
);

-- ============================================================
-- Migración 009: tabla email_audit
-- ============================================================

CREATE TABLE IF NOT EXISTS email_audit (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(255),
    email_to VARCHAR(255) NOT NULL,
    email_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ
);
