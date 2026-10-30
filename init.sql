-- ============================================================
--  init.sql — схема БД (выполняется при первом старте Postgres)
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    user_id     BIGINT PRIMARY KEY,
    username    TEXT,
    full_name   TEXT,
    lang        TEXT DEFAULT 'ru',
    first_seen  TIMESTAMP DEFAULT NOW(),
    last_seen   TIMESTAMP DEFAULT NOW(),
    msg_count   INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS questions (
    id              SERIAL PRIMARY KEY,
    sender_id       BIGINT NOT NULL,
    sender_name     TEXT,
    sender_username TEXT,
    question        TEXT,
    answer          TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    answered_at     TIMESTAMP,
    is_answered     BOOLEAN DEFAULT FALSE,
    media_type      TEXT,
    media_file_id   TEXT,
    owner_msg_id    BIGINT,
    reactions       INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS scheduled (
    id       SERIAL PRIMARY KEY,
    qid      INT,
    answer   TEXT,
    send_at  TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chats (
    id          SERIAL PRIMARY KEY,
    question_id INT,
    user_id     BIGINT,
    owner_id    BIGINT,
    created_at  TIMESTAMP DEFAULT NOW(),
    closed      BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          SERIAL PRIMARY KEY,
    chat_id     INT,
    sender_role TEXT,
    text        TEXT,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reactions_log (
    id          SERIAL PRIMARY KEY,
    question_id INT REFERENCES questions(id) ON DELETE CASCADE,
    user_id     BIGINT,
    emoji       TEXT,
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(question_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_questions_answered ON questions(is_answered);
CREATE INDEX IF NOT EXISTS idx_questions_created  ON questions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scheduled_send_at  ON scheduled(send_at);
CREATE INDEX IF NOT EXISTS idx_chats_closed       ON chats(closed);
CREATE INDEX IF NOT EXISTS idx_reactions_qid      ON reactions_log(question_id);