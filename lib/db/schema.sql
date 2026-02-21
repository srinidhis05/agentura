-- Wealth Copilot Database Schema
-- ===============================
--
-- PostgreSQL schema for learning, risk tracking, and goals.
-- Ported from: FinceptTerminal/voltagent/src/memory/schema.ts
-- Enhanced with: Goals, currency tracking, cross-border fields

-- ============================================================================
-- TRADES & LEARNING
-- ============================================================================

-- Trades table: records all executed trades
CREATE TABLE IF NOT EXISTS trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  symbol VARCHAR(50) NOT NULL,
  exchange VARCHAR(20) NOT NULL,
  action VARCHAR(10) NOT NULL,  -- BUY, SELL
  entry_price DECIMAL(18,6) NOT NULL,
  exit_price DECIMAL(18,6),
  quantity INTEGER NOT NULL,
  currency VARCHAR(3) NOT NULL DEFAULT 'INR',
  pnl DECIMAL(18,6),
  pnl_pct DECIMAL(8,4),
  outcome VARCHAR(20),  -- profit, loss, stopped_out, target_hit
  hold_days INTEGER,
  recommendation VARCHAR(20),
  score DECIMAL(4,2),
  reasons JSONB,  -- array of strings
  goal_id UUID REFERENCES goals(id),
  broker VARCHAR(20) NOT NULL DEFAULT 'paper',
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  closed_at TIMESTAMPTZ
);

CREATE INDEX idx_trades_user ON trades(user_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_outcome ON trades(outcome);
CREATE INDEX idx_trades_goal ON trades(goal_id);

-- Patterns table: learned patterns from outcomes
CREATE TABLE IF NOT EXISTS patterns (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  pattern_type VARCHAR(50) NOT NULL,  -- recommendation, reason, scenario, sector
  pattern_value VARCHAR(200) NOT NULL,
  total_trades INTEGER DEFAULT 0,
  wins INTEGER DEFAULT 0,
  losses INTEGER DEFAULT 0,
  avg_pnl_pct DECIMAL(8,4) DEFAULT 0,
  win_rate DECIMAL(5,4) DEFAULT 0,
  last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, pattern_type, pattern_value)
);

CREATE INDEX idx_patterns_user ON patterns(user_id);
CREATE INDEX idx_patterns_type ON patterns(pattern_type);

-- Feedback table: human feedback on trades
CREATE TABLE IF NOT EXISTS feedback (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  trade_id UUID NOT NULL REFERENCES trades(id),
  feedback_type VARCHAR(50) NOT NULL,  -- diagnosis_incorrect, stop_too_tight, etc.
  details TEXT,
  suggestion TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feedback_trade ON feedback(trade_id);

-- Daily stats table: aggregate daily performance
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

-- ============================================================================
-- RISK MANAGEMENT
-- ============================================================================

-- Risk events table: audit trail for all risk decisions
CREATE TABLE IF NOT EXISTS risk_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  event_type VARCHAR(50) NOT NULL,  -- check, violation, halt, warning
  signal_id UUID,
  rule VARCHAR(100),
  limit_value VARCHAR(50),
  actual_value VARCHAR(50),
  decision VARCHAR(20),  -- approved, blocked, halted
  reason TEXT,
  portfolio_snapshot JSONB
);

CREATE INDEX idx_risk_events_user ON risk_events(user_id);
CREATE INDEX idx_risk_events_type ON risk_events(event_type);
CREATE INDEX idx_risk_events_timestamp ON risk_events(timestamp);

-- Circuit breaker state
CREATE TABLE IF NOT EXISTS circuit_breaker (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) UNIQUE,
  is_halted BOOLEAN DEFAULT FALSE,
  reason TEXT,
  halted_at TIMESTAMPTZ,
  resumes_at TIMESTAMPTZ
);

-- ============================================================================
-- GOALS (Cross-Border)
-- ============================================================================

-- Goals table: user financial goals
CREATE TABLE IF NOT EXISTS goals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  name VARCHAR(200) NOT NULL,
  description TEXT,
  target_amount DECIMAL(18,6) NOT NULL,
  target_currency VARCHAR(3) NOT NULL,
  current_amount DECIMAL(18,6) DEFAULT 0,
  target_date DATE NOT NULL,
  risk_profile VARCHAR(20) NOT NULL,  -- conservative, moderate, aggressive
  priority VARCHAR(20) NOT NULL DEFAULT 'important',  -- critical, important, flexible
  status VARCHAR(20) DEFAULT 'active',  -- active, paused, completed
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_goals_user ON goals(user_id);
CREATE INDEX idx_goals_status ON goals(status);

-- Goal allocations: target asset allocation per goal
CREATE TABLE IF NOT EXISTS goal_allocations (
  id SERIAL PRIMARY KEY,
  goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
  asset_class VARCHAR(20) NOT NULL,  -- equity, debt, gold, crypto, cash
  market VARCHAR(20) NOT NULL,  -- india, us, uk, uae, singapore
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
  fx_rate_to_target DECIMAL(12,6),  -- FX rate at time of recording
  notes TEXT
);

-- ============================================================================
-- CROSS-BORDER
-- ============================================================================

-- FX rate history (for tracking currency impact)
CREATE TABLE IF NOT EXISTS fx_rates (
  id SERIAL PRIMARY KEY,
  from_currency VARCHAR(3) NOT NULL,
  to_currency VARCHAR(3) NOT NULL,
  rate DECIMAL(12,6) NOT NULL,
  recorded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(from_currency, to_currency, recorded_at)
);

CREATE INDEX idx_fx_rates_pair ON fx_rates(from_currency, to_currency);
CREATE INDEX idx_fx_rates_time ON fx_rates(recorded_at);

-- Remittance recommendations
CREATE TABLE IF NOT EXISTS remittance_recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  from_currency VARCHAR(3) NOT NULL,
  to_currency VARCHAR(3) NOT NULL,
  amount DECIMAL(18,6) NOT NULL,
  recommended_rate DECIMAL(12,6),
  current_rate DECIMAL(12,6),
  recommendation TEXT,  -- wait, transfer_now, split
  confidence DECIMAL(5,4),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  valid_until TIMESTAMPTZ
);

-- ============================================================================
-- GEOPOLITICS
-- ============================================================================

-- Active geopolitical scenarios
CREATE TABLE IF NOT EXISTS active_scenarios (
  id SERIAL PRIMARY KEY,
  scenario_id VARCHAR(50) NOT NULL,
  detected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  source TEXT,  -- news headline that triggered
  expires_at TIMESTAMPTZ,
  UNIQUE(scenario_id, detected_at)
);

-- Scenario impact log
CREATE TABLE IF NOT EXISTS scenario_impacts (
  id SERIAL PRIMARY KEY,
  scenario_id VARCHAR(50) NOT NULL,
  user_id UUID NOT NULL REFERENCES users(id),
  impact_type VARCHAR(20) NOT NULL,  -- position_adjustment, alert, rebalance
  details JSONB,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- USERS (Minimal - Auth handled by Clerk)
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_id VARCHAR(200) UNIQUE NOT NULL,
  email VARCHAR(255),
  base_currency VARCHAR(3) NOT NULL DEFAULT 'INR',
  risk_profile VARCHAR(20) DEFAULT 'moderate',
  onboarding_complete BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- User settings
CREATE TABLE IF NOT EXISTS user_settings (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) UNIQUE,
  notification_preferences JSONB DEFAULT '{"push": true, "email": true}',
  human_approval_threshold JSONB DEFAULT '{"INR": 50000, "USD": 500}',
  markets_enabled JSONB DEFAULT '["india"]',
  brokers_connected JSONB DEFAULT '[]',
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Update pattern stats on trade close
CREATE OR REPLACE FUNCTION update_patterns_on_trade_close()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.closed_at IS NOT NULL AND OLD.closed_at IS NULL THEN
    -- Update recommendation pattern
    INSERT INTO patterns (user_id, pattern_type, pattern_value, total_trades, wins, losses, avg_pnl_pct, win_rate)
    VALUES (
      NEW.user_id,
      'recommendation',
      NEW.recommendation,
      1,
      CASE WHEN NEW.pnl > 0 THEN 1 ELSE 0 END,
      CASE WHEN NEW.pnl <= 0 THEN 1 ELSE 0 END,
      NEW.pnl_pct,
      CASE WHEN NEW.pnl > 0 THEN 1.0 ELSE 0.0 END
    )
    ON CONFLICT (user_id, pattern_type, pattern_value) DO UPDATE SET
      total_trades = patterns.total_trades + 1,
      wins = patterns.wins + CASE WHEN NEW.pnl > 0 THEN 1 ELSE 0 END,
      losses = patterns.losses + CASE WHEN NEW.pnl <= 0 THEN 1 ELSE 0 END,
      avg_pnl_pct = (patterns.avg_pnl_pct * patterns.total_trades + NEW.pnl_pct) / (patterns.total_trades + 1),
      win_rate = (patterns.wins + CASE WHEN NEW.pnl > 0 THEN 1 ELSE 0 END)::DECIMAL / (patterns.total_trades + 1),
      last_updated = CURRENT_TIMESTAMP;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_patterns
  AFTER UPDATE ON trades
  FOR EACH ROW
  EXECUTE FUNCTION update_patterns_on_trade_close();

-- Update daily stats on trade close
CREATE OR REPLACE FUNCTION update_daily_stats_on_trade_close()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.closed_at IS NOT NULL AND OLD.closed_at IS NULL THEN
    INSERT INTO daily_stats (user_id, date, total_trades, wins, losses, gross_pnl, currency)
    VALUES (
      NEW.user_id,
      CURRENT_DATE,
      1,
      CASE WHEN NEW.pnl > 0 THEN 1 ELSE 0 END,
      CASE WHEN NEW.pnl <= 0 THEN 1 ELSE 0 END,
      NEW.pnl,
      NEW.currency
    )
    ON CONFLICT (user_id, date) DO UPDATE SET
      total_trades = daily_stats.total_trades + 1,
      wins = daily_stats.wins + CASE WHEN NEW.pnl > 0 THEN 1 ELSE 0 END,
      losses = daily_stats.losses + CASE WHEN NEW.pnl <= 0 THEN 1 ELSE 0 END,
      gross_pnl = daily_stats.gross_pnl + NEW.pnl,
      win_rate = (daily_stats.wins + CASE WHEN NEW.pnl > 0 THEN 1 ELSE 0 END)::DECIMAL / (daily_stats.total_trades + 1);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_daily_stats
  AFTER UPDATE ON trades
  FOR EACH ROW
  EXECUTE FUNCTION update_daily_stats_on_trade_close();
