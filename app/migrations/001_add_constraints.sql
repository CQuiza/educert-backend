-- ============================================================
-- Migración 001: CHECK constraints + NOT NULL en name/first_last_name
-- Aplicar con: psql -U crtquiza -d certify -f migrations/001_add_constraints.sql
-- ============================================================

BEGIN;

-- ==================== users ====================

-- name y first_last_name → NOT NULL
-- (actualizar filas con NULL antes de aplicar, si las hubiera)
UPDATE users SET name = 'Sin nombre' WHERE name IS NULL;
UPDATE users SET first_last_name = 'Sin apellido' WHERE first_last_name IS NULL;

ALTER TABLE users
    ALTER COLUMN name SET NOT NULL,
    ALTER COLUMN first_last_name SET NOT NULL;

-- CHECK: role
ALTER TABLE users
    ADD CONSTRAINT ck_users_role
    CHECK (role IN ('superuser', 'admin', 'teacher', 'student'));

-- CHECK: identity_type
ALTER TABLE users
    ADD CONSTRAINT ck_users_identity_type
    CHECK (identity_type IN ('CC', 'TI', 'OTHER'));


-- ==================== courses ====================

-- CHECK: status
ALTER TABLE courses
    ADD CONSTRAINT ck_courses_status
    CHECK (status IN ('draft', 'published', 'archived'));


-- ==================== certificate_types ====================

-- CHECK: type
ALTER TABLE certificate_types
    ADD CONSTRAINT ck_certificate_types_type
    CHECK (type IN ('basic', 'advanced', 'diploma'));

-- CHECK: validity_type
ALTER TABLE certificate_types
    ADD CONSTRAINT ck_certificate_types_validity_type
    CHECK (validity_type IN ('years', 'months', 'days'));


-- ==================== certificates ====================

-- CHECK: status
ALTER TABLE certificates
    ADD CONSTRAINT ck_certificates_status
    CHECK (status IN ('active', 'revoked', 'expired'));


COMMIT;
