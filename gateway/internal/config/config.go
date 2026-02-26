package config

import (
	"fmt"
	"os"
	"strings"

	"gopkg.in/yaml.v3"
)

type Config struct {
	Server     ServerConfig     `yaml:"server"`
	Database   DatabaseConfig   `yaml:"database"`
	Agent      AgentConfig      `yaml:"agent"`
	MarketData MarketDataConfig `yaml:"market_data"`
	Broker     BrokerConfig     `yaml:"broker"`
	Auth       AuthConfig       `yaml:"auth"`
	CORS       CORSConfig       `yaml:"cors"`
	RateLimit  RateLimitConfig  `yaml:"rate_limit"`
	Logging    LoggingConfig    `yaml:"logging"`
	Metrics    MetricsConfig    `yaml:"metrics"`
	Executor   ExecutorConfig   `yaml:"executor"`
	Triggers   TriggersConfig   `yaml:"triggers"`
}

type TriggersConfig struct {
	Enabled  bool                `yaml:"enabled"`
	Timezone string              `yaml:"timezone"`
	Cron     CronConfig          `yaml:"cron"`
	Webhook  WebhookConfig       `yaml:"webhook"`
	GitHub   GitHubWebhookConfig `yaml:"github"`
}

type GitHubWebhookConfig struct {
	Enabled bool   `yaml:"enabled"`
	Secret  string `yaml:"secret"`
}

type CronConfig struct {
	Enabled      bool `yaml:"enabled"`
	PollInterval int  `yaml:"poll_interval"` // seconds
}

type WebhookConfig struct {
	Enabled bool   `yaml:"enabled"`
	Secret  string `yaml:"secret"`
}

type ExecutorConfig struct {
	URL     string `yaml:"url"`
	Timeout int    `yaml:"timeout"` // seconds
}

type ServerConfig struct {
	Host string `yaml:"host"`
	Port int    `yaml:"port"`
}

func (s ServerConfig) Addr() string {
	return fmt.Sprintf("%s:%d", s.Host, s.Port)
}

type DatabaseConfig struct {
	Host     string `yaml:"host"`
	Port     int    `yaml:"port"`
	User     string `yaml:"user"`
	Password string `yaml:"password"`
	Name     string `yaml:"name"`
	SSLMode  string `yaml:"ssl_mode"`
}

func (d DatabaseConfig) DSN() string {
	return fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
		d.Host, d.Port, d.User, d.Password, d.Name, d.SSLMode)
}

type AgentConfig struct {
	GRPCAddr string `yaml:"grpc_addr"`
}

type MarketDataConfig struct {
	Provider string `yaml:"provider"`
}

type BrokerConfig struct {
	Mode string `yaml:"mode"` // paper or live
}

type AuthConfig struct {
	ClerkSecretKey string `yaml:"clerk_secret_key"`
	Enabled        bool   `yaml:"enabled"`
}

type CORSConfig struct {
	AllowedOrigins []string `yaml:"allowed_origins"`
}

type RateLimitConfig struct {
	RequestsPerSecond float64 `yaml:"requests_per_second"`
	Burst             int     `yaml:"burst"`
}

type LoggingConfig struct {
	Level  string `yaml:"level"`
	Format string `yaml:"format"` // json or text
}

type MetricsConfig struct {
	Enabled bool   `yaml:"enabled"`
	Path    string `yaml:"path"`
}

// Load reads config from a YAML file and expands ${ENV_VAR} references.
func Load(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("reading config %s: %w", path, err)
	}

	expanded := expandEnvVars(string(data))

	var cfg Config
	if err := yaml.Unmarshal([]byte(expanded), &cfg); err != nil {
		return nil, fmt.Errorf("parsing config %s: %w", path, err)
	}

	applyDefaults(&cfg)
	return &cfg, nil
}

func expandEnvVars(s string) string {
	return os.Expand(s, func(key string) string {
		if val, ok := os.LookupEnv(key); ok {
			return val
		}
		return "${" + key + "}"
	})
}

func applyDefaults(cfg *Config) {
	if cfg.Server.Host == "" {
		cfg.Server.Host = "0.0.0.0"
	}
	if cfg.Server.Port == 0 {
		cfg.Server.Port = 8080
	}
	if cfg.Database.SSLMode == "" {
		cfg.Database.SSLMode = "disable"
	}
	if cfg.Broker.Mode == "" {
		cfg.Broker.Mode = "paper"
	}
	if cfg.Logging.Level == "" {
		cfg.Logging.Level = "info"
	}
	if cfg.Logging.Format == "" {
		cfg.Logging.Format = "json"
	}
	if cfg.Metrics.Path == "" {
		cfg.Metrics.Path = "/metrics"
	}
	if cfg.RateLimit.RequestsPerSecond == 0 {
		cfg.RateLimit.RequestsPerSecond = 10
	}
	if cfg.RateLimit.Burst == 0 {
		cfg.RateLimit.Burst = 20
	}
	if len(cfg.CORS.AllowedOrigins) == 0 {
		cfg.CORS.AllowedOrigins = []string{"*"}
	}
	if cfg.Executor.URL == "" {
		cfg.Executor.URL = "http://localhost:8000"
	}
	if cfg.Executor.Timeout == 0 {
		cfg.Executor.Timeout = 120
	}

	// Triggers defaults
	if cfg.Triggers.Timezone == "" {
		cfg.Triggers.Timezone = "UTC"
	}
	if cfg.Triggers.Cron.PollInterval == 0 {
		cfg.Triggers.Cron.PollInterval = 300
	}
}

// LoadWithOverrides loads a base config and optionally merges overrides.
func LoadWithOverrides(basePath, overridePath string) (*Config, error) {
	cfg, err := Load(basePath)
	if err != nil {
		return nil, err
	}

	if overridePath == "" {
		return cfg, nil
	}

	if _, err := os.Stat(overridePath); os.IsNotExist(err) {
		return cfg, nil
	}

	_ = strings.TrimSpace(overridePath) // override loading is a future enhancement
	return cfg, nil
}
