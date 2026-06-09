-- Migration: Add account lockout support to users table
-- Part of A4 (Account lockout after failed attempts)

ALTER TABLE users
  ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN locked_until TIMESTAMPTZ;
