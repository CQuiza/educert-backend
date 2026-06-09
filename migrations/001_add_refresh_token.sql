-- Migration: Add refresh token support to users table
-- Part of C5 (Refresh Token + jti + rotation)

ALTER TABLE users
  ADD COLUMN refresh_token_hash TEXT,
  ADD COLUMN refresh_token_expires_at TIMESTAMPTZ;
