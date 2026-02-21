-- FX rate history
CREATE TABLE IF NOT EXISTS fx_rates (
  id SERIAL PRIMARY KEY,
  from_currency VARCHAR(3) NOT NULL,
  to_currency VARCHAR(3) NOT NULL,
  rate DECIMAL(12,6) NOT NULL,
  recorded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(from_currency, to_currency, recorded_at)
);

CREATE INDEX IF NOT EXISTS idx_fx_rates_pair ON fx_rates(from_currency, to_currency);
CREATE INDEX IF NOT EXISTS idx_fx_rates_time ON fx_rates(recorded_at);

-- Remittance recommendations
CREATE TABLE IF NOT EXISTS remittance_recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  from_currency VARCHAR(3) NOT NULL,
  to_currency VARCHAR(3) NOT NULL,
  amount DECIMAL(18,6) NOT NULL,
  recommended_rate DECIMAL(12,6),
  current_rate DECIMAL(12,6),
  recommendation TEXT,
  confidence DECIMAL(5,4),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  valid_until TIMESTAMPTZ
);
