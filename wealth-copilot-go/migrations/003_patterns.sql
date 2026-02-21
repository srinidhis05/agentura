-- Patterns table: learned patterns from outcomes
CREATE TABLE IF NOT EXISTS patterns (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  pattern_type VARCHAR(50) NOT NULL,
  pattern_value VARCHAR(200) NOT NULL,
  total_trades INTEGER DEFAULT 0,
  wins INTEGER DEFAULT 0,
  losses INTEGER DEFAULT 0,
  avg_pnl_pct DECIMAL(8,4) DEFAULT 0,
  win_rate DECIMAL(5,4) DEFAULT 0,
  last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, pattern_type, pattern_value)
);

CREATE INDEX IF NOT EXISTS idx_patterns_user ON patterns(user_id);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type);

-- Feedback table: human feedback on trades
CREATE TABLE IF NOT EXISTS feedback (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  trade_id UUID NOT NULL REFERENCES trades(id),
  feedback_type VARCHAR(50) NOT NULL,
  details TEXT,
  suggestion TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_trade ON feedback(trade_id);
