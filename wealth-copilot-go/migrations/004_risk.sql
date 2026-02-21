-- Risk events table: audit trail for all risk decisions
CREATE TABLE IF NOT EXISTS risk_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  event_type VARCHAR(50) NOT NULL,
  signal_id UUID,
  rule VARCHAR(100),
  limit_value VARCHAR(50),
  actual_value VARCHAR(50),
  decision VARCHAR(20),
  reason TEXT,
  portfolio_snapshot JSONB
);

CREATE INDEX IF NOT EXISTS idx_risk_events_user ON risk_events(user_id);
CREATE INDEX IF NOT EXISTS idx_risk_events_type ON risk_events(event_type);
CREATE INDEX IF NOT EXISTS idx_risk_events_timestamp ON risk_events(timestamp);

-- Circuit breaker state
CREATE TABLE IF NOT EXISTS circuit_breaker (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) UNIQUE,
  is_halted BOOLEAN DEFAULT FALSE,
  reason TEXT,
  halted_at TIMESTAMPTZ,
  resumes_at TIMESTAMPTZ
);
