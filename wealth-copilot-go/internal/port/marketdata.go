package port

import (
	"context"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

type MarketDataPort interface {
	GetPrice(ctx context.Context, symbol string, exchange domain.Exchange) (*domain.Price, error)
	GetPrices(ctx context.Context, symbols []string) (map[string]domain.Price, error)
	GetFundamentals(ctx context.Context, symbol string) (*domain.Fundamentals, error)
	GetTechnicals(ctx context.Context, symbol string, period string) (*domain.Technicals, error)
}
