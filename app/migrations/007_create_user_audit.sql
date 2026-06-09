-- Tabla de auditoría: snapshot completo del usuario y sus relaciones al ser eliminado
CREATE TABLE user_audit (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    deleted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    snapshot JSONB NOT NULL
);
