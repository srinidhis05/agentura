-- Trades table: records all executed trades
CREATE TABLE IF NOT EXISTS trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  symbol VARCHAR(50) NOT NULL,
  exchange VARCHAR(20) NOT NULL,
  action VARCHAR(10) NOT NULL,
  entry_price DECIMAL(18,6) NOT NULL,
  exit_price DECIMAL(18,6),
  quantity INTEGER NOT NULL,
  currency VARCHAR(3) NOT NULL DEFAULT 'INR',
  pnl DECIMAL(18,6),
  pnl_pct DECIMAL(8,4),
  outcome VARCHAR(20),
  hold_days INTEGER,
  recommendation VARCHAR(20),
  score DECIMAL(4,2),
  reasons JSONB,
  goal_id UUID REFERENCES goals(id),
  broker VARCHAR(20) NOT NULL DEFAULT 'paper',
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  closed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_trades_user ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_outcome ON trades(outcome);
CREATE INDEX IF NOT EXISTS idx_trades_goal ON trades(goal_id);

-- Daily stats table
CREATE TABLE IF NOT EXISTS daily_stats (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  date DATE NOT NULL,
  total_trades INTEGER DEFAULT 0,
  wins INTEGER DEFAULT 0,
  losses INTEGER DEFAULT 0,
  gross_pnl DECIMAL(18,6) DEFAULT 0,
  currency VARCHAR(3) NOT NULL DEFAULT 'INR',
  win_rate DECIMAL(5,4) DEFAULT 0,
  sharpe DECIMAL(6,4) DEFAULT 0,
  UNIQUE(user_id, date)
);
