package port

import (
	"context"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

type CrossBorderPort interface {
	GetFxRate(ctx context.Context, from, to domain.Currency) (domain.FxRate, error)
	GetFxRates(ctx context.Context, baseCurrency domain.Currency) (map[domain.Currency]domain.FxRate, error)
	CalculateCurrencyImpact(ctx context.Context, symbol string, baseCurrency domain.Currency, period domain.CurrencyImpactPeriod) (domain.CurrencyImpact, error)
	GetOptimalRemittanceTime(ctx context.Context, from, to domain.Currency, amount float64) (domain.RemittanceRecommendation, error)
}
