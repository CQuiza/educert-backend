-- ============================================================
-- Migración 012: Evaluaciones por módulo.
-- Aplicar: psql ... -f migrations/012_create_assessments.sql
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS module_assessments (
    id            INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    module_id     INTEGER NOT NULL UNIQUE REFERENCES modules(id) ON DELETE CASCADE,
    passing_score INTEGER NOT NULL DEFAULT 70 CHECK (passing_score >= 1 AND passing_score <= 100)
);

CREATE TABLE IF NOT EXISTS assessment_questions (
    id             INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    assessment_id  INTEGER NOT NULL REFERENCES module_assessments(id) ON DELETE CASCADE,
    question_text  TEXT NOT NULL,
    question_type  VARCHAR(20) NOT NULL CHECK (question_type IN ('multiple_choice', 'true_false')),
    points         INTEGER NOT NULL DEFAULT 1 CHECK (points >= 1),
    order_index    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS assessment_options (
    id            INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    question_id   INTEGER NOT NULL REFERENCES assessment_questions(id) ON DELETE CASCADE,
    option_text   VARCHAR(255) NOT NULL,
    is_correct    BOOLEAN NOT NULL DEFAULT false,
    UNIQUE(question_id, option_text)
);

CREATE TABLE IF NOT EXISTS user_assessment_attempts (
    id             INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    assessment_id  INTEGER NOT NULL REFERENCES module_assessments(id) ON DELETE CASCADE,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score          NUMERIC(5,2) NOT NULL DEFAULT 0,
    passed         BOOLEAN NOT NULL DEFAULT false,
    started_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at    TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS user_assessment_answers (
    id                  INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    attempt_id          INTEGER NOT NULL REFERENCES user_assessment_attempts(id) ON DELETE CASCADE,
    question_id         INTEGER NOT NULL REFERENCES assessment_questions(id) ON DELETE CASCADE,
    selected_option_id  INTEGER NOT NULL REFERENCES assessment_options(id) ON DELETE CASCADE,
    is_correct          BOOLEAN NOT NULL DEFAULT false,
    UNIQUE(attempt_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_assessment_questions_assessment
    ON assessment_questions (assessment_id);

CREATE INDEX IF NOT EXISTS idx_assessment_options_question
    ON assessment_options (question_id);

CREATE INDEX IF NOT EXISTS idx_attempts_assessment
    ON user_assessment_attempts (assessment_id);

CREATE INDEX IF NOT EXISTS idx_attempts_user
    ON user_assessment_attempts (user_id);

CREATE INDEX IF NOT EXISTS idx_answers_attempt
    ON user_assessment_answers (attempt_id);

COMMIT;
