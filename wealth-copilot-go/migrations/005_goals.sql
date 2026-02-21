-- Goals table
CREATE TABLE IF NOT EXISTS goals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  name VARCHAR(200) NOT NULL,
  description TEXT,
  target_amount DECIMAL(18,6) NOT NULL,
  target_currency VARCHAR(3) NOT NULL,
  current_amount DECIMAL(18,6) DEFAULT 0,
  target_date DATE NOT NULL,
  risk_profile VARCHAR(20) NOT NULL,
  priority VARCHAR(20) NOT NULL DEFAULT 'important',
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);

-- Goal allocations
CREATE TABLE IF NOT EXISTS goal_allocations (
  id SERIAL PRIMARY KEY,
  goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
  asset_class VARCHAR(20) NOT NULL,
  market VARCHAR(20) NOT NULL,
  target_pct DECIMAL(5,2) NOT NULL,
  current_pct DECIMAL(5,2) DEFAULT 0,
  currency VARCHAR(3) NOT NULL,
  UNIQUE(goal_id, asset_class, market)
);

-- Goal progress history
CREATE TABLE IF NOT EXISTS goal_progress (
  id SERIAL PRIMARY KEY,
  goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
  recorded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  amount DECIMAL(18,6) NOT NULL,
  currency VARCHAR(3) NOT NULL,
  fx_rate_to_target DECIMAL(12,6),
  notes TEXT
);
