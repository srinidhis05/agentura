package postgres

import (
	"fmt"
	"log/slog"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

func NewDB(dsn string) (*gorm.DB, error) {
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Silent),
	})
	if err != nil {
		return nil, fmt.Errorf("connecting to database: %w", err)
	}

	sqlDB, err := db.DB()
	if err != nil {
		return nil, fmt.Errorf("getting sql.DB: %w", err)
	}

	sqlDB.SetMaxOpenConns(25)
	sqlDB.SetMaxIdleConns(5)

	slog.Info("database connected")
	return db, nil
}

func AutoMigrate(db *gorm.DB) error {
	return db.AutoMigrate(
		&UserModel{},
		&UserSettingsModel{},
		&TradeModel{},
		&PatternModel{},
		&FeedbackModel{},
		&DailyStatsModel{},
		&RiskEventModel{},
		&CircuitBreakerModel{},
		&GoalModel{},
		&GoalAllocationModel{},
		&GoalProgressModel{},
		&FxRateModel{},
		&ActiveScenarioModel{},
	)
}

// HealthCheck pings the database.
func HealthCheck(db *gorm.DB) func() error {
	return func() error {
		sqlDB, err := db.DB()
		if err != nil {
			return err
		}
		return sqlDB.Ping()
	}
}
