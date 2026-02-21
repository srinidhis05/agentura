-- Active geopolitical scenarios
CREATE TABLE IF NOT EXISTS active_scenarios (
  id SERIAL PRIMARY KEY,
  scenario_id VARCHAR(50) NOT NULL,
  detected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  source TEXT,
  expires_at TIMESTAMPTZ,
  UNIQUE(scenario_id, detected_at)
);

-- Scenario impact log
CREATE TABLE IF NOT EXISTS scenario_impacts (
  id SERIAL PRIMARY KEY,
  scenario_id VARCHAR(50) NOT NULL,
  user_id UUID NOT NULL REFERENCES users(id),
  impact_type VARCHAR(20) NOT NULL,
  details JSONB,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
