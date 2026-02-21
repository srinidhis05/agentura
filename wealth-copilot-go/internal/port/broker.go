package port

import (
	"context"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

type BrokerPort interface {
	Name() string
	IsConnected(ctx context.Context) (bool, error)
	Buy(ctx context.Context, symbol string, exchange domain.Exchange, quantity int, orderType domain.OrderType, price *float64) (domain.Order, error)
	Sell(ctx context.Context, symbol string, exchange domain.Exchange, quantity int, orderType domain.OrderType, price *float64) (domain.Order, error)
	SetStopLoss(ctx context.Context, symbol string, exchange domain.Exchange, quantity int, triggerPrice float64) (domain.Order, error)
	GetPortfolio(ctx context.Context) (domain.Portfolio, error)
	GetOrders(ctx context.Context) ([]domain.Order, error)
}
