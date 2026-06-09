-- ============================================================
-- Migración 004: tabla worker_audit para auditoría de
-- trabajos en segundo plano (Celery).
-- Aplicar: psql ... -f migrations/004_create_worker_audit.sql
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS worker_audit (
    id          INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    task_name   VARCHAR(100) NOT NULL,
    status      VARCHAR(20) NOT NULL,
    started_at  TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    details     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_worker_audit_task_name
    ON worker_audit (task_name);

CREATE INDEX IF NOT EXISTS idx_worker_audit_status
    ON worker_audit (status);

CREATE INDEX IF NOT EXISTS idx_worker_audit_created_at
    ON worker_audit (created_at);

COMMIT;
