

CREATE TABLE IF NOT EXISTS query_history (
    id              SERIAL PRIMARY KEY,
    question        TEXT NOT NULL,
    generated_sql   TEXT,
    row_count       INTEGER,
    attempts        INTEGER DEFAULT 1,
    status          VARCHAR(20) NOT NULL,   -- 'success', 'failed', 'ambiguous'
    error_message   TEXT,
    explanation     TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_query_history_created_at
    ON query_history (created_at DESC);