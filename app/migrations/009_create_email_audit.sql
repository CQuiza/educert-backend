-- Tabla de auditoría de envío de correos electrónicos
CREATE TABLE email_audit (
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
