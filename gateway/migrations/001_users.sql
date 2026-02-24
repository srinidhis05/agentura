-- Users (Auth handled by Clerk)
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
