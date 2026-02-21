package broker

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
	"github.com/wealth-copilot/wealth-copilot-go/internal/port"
)

// Paper implements BrokerPort as an in-memory paper trading broker.
type Paper struct {
	mu         sync.RWMutex
	marketData port.MarketDataPort
	orders     []domain.Order
	positions  map[string]*domain.Position // symbol → position
	cash       domain.Money
	nextID     int
}

func NewPaper(md port.MarketDataPort, initialCash domain.Money) *Paper {
	return &Paper{
		marketData: md,
		orders:     make([]domain.Order, 0),
		positions:  make(map[string]*domain.Position),
		cash:       initialCash,
	}
}

func (p *Paper) Name() string { return "paper" }

func (p *Paper) IsConnected(_ context.Context) (bool, error) { return true, nil }

func (p *Paper) Buy(ctx context.Context, symbol string, exchange domain.Exchange, quantity int, _ domain.OrderType, price *float64) (domain.Order, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	execPrice, err := p.resolvePrice(ctx, symbol, exchange, price)
	if err != nil {
		return domain.Order{}, err
	}

	cost := execPrice * float64(quantity)
	if cost > p.cash.Amount {
		return domain.Order{}, fmt.Errorf("insufficient cash: need %.2f, have %.2f", cost, p.cash.Amount)
	}

	p.cash.Amount -= cost
	p.nextID++

	// Update or create position
	if pos, ok := p.positions[symbol]; ok {
		totalQty := pos.Quantity + quantity
		pos.AvgPrice = (pos.AvgPrice*float64(pos.Quantity) + execPrice*float64(quantity)) / float64(totalQty)
		pos.Quantity = totalQty
		pos.CurrentPrice = execPrice
	} else {
		p.positions[symbol] = &domain.Position{
			Symbol:       symbol,
			Exchange:     exchange,
			Quantity:     quantity,
			AvgPrice:     execPrice,
			CurrentPrice: execPrice,
			Currency:     p.cash.Currency,
		}
	}

	order := domain.Order{
		ID:        fmt.Sprintf("paper-%d", p.nextID),
		Timestamp: time.Now(),
		Action:    domain.ActionBUY,
		Symbol:    symbol,
		Exchange:  exchange,
		Quantity:  quantity,
		Price:     execPrice,
		Status:    domain.OrderStatusFilled,
		Broker:    domain.BrokerPaper,
		Currency:  p.cash.Currency,
	}
	p.orders = append(p.orders, order)
	return order, nil
}

func (p *Paper) Sell(ctx context.Context, symbol string, exchange domain.Exchange, quantity int, _ domain.OrderType, price *float64) (domain.Order, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	pos, ok := p.positions[symbol]
	if !ok || pos.Quantity < quantity {
		return domain.Order{}, fmt.Errorf("insufficient position: have %d, need %d", p.positionQty(symbol), quantity)
	}

	execPrice, err := p.resolvePrice(ctx, symbol, exchange, price)
	if err != nil {
		return domain.Order{}, err
	}

	p.cash.Amount += execPrice * float64(quantity)
	pos.Quantity -= quantity
	if pos.Quantity == 0 {
		delete(p.positions, symbol)
	}

	p.nextID++
	order := domain.Order{
		ID:        fmt.Sprintf("paper-%d", p.nextID),
		Timestamp: time.Now(),
		Action:    domain.ActionSELL,
		Symbol:    symbol,
		Exchange:  exchange,
		Quantity:  quantity,
		Price:     execPrice,
		Status:    domain.OrderStatusFilled,
		Broker:    domain.BrokerPaper,
		Currency:  p.cash.Currency,
	}
	p.orders = append(p.orders, order)
	return order, nil
}

func (p *Paper) SetStopLoss(_ context.Context, symbol string, exchange domain.Exchange, quantity int, triggerPrice float64) (domain.Order, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	p.nextID++
	order := domain.Order{
		ID:        fmt.Sprintf("paper-sl-%d", p.nextID),
		Timestamp: time.Now(),
		Action:    domain.ActionSELL,
		Symbol:    symbol,
		Exchange:  exchange,
		Quantity:  quantity,
		Price:     triggerPrice,
		Status:    domain.OrderStatusPending,
		Broker:    domain.BrokerPaper,
		Currency:  p.cash.Currency,
	}
	p.orders = append(p.orders, order)
	return order, nil
}

func (p *Paper) GetPortfolio(_ context.Context) (domain.Portfolio, error) {
	p.mu.RLock()
	defer p.mu.RUnlock()

	positions := make([]domain.Position, 0, len(p.positions))
	positionsValue := 0.0
	for _, pos := range p.positions {
		pnlAmt := (pos.CurrentPrice - pos.AvgPrice) * float64(pos.Quantity)
		pnlPct := 0.0
		if pos.AvgPrice > 0 {
			pnlPct = ((pos.CurrentPrice - pos.AvgPrice) / pos.AvgPrice) * 100
		}
		positions = append(positions, domain.Position{
			Symbol:       pos.Symbol,
			Exchange:     pos.Exchange,
			Quantity:     pos.Quantity,
			AvgPrice:     pos.AvgPrice,
			CurrentPrice: pos.CurrentPrice,
			PnL:          domain.Money{Amount: pnlAmt, Currency: p.cash.Currency},
			PnLPct:       domain.Percentage{Value: pnlPct},
			Currency:     p.cash.Currency,
		})
		positionsValue += pos.CurrentPrice * float64(pos.Quantity)
	}

	totalValue := p.cash.Amount + positionsValue

	return domain.Portfolio{
		Cash:       p.cash,
		Positions:  positions,
		TotalValue: domain.Money{Amount: totalValue, Currency: p.cash.Currency},
		DailyPnL:   domain.Money{Amount: 0, Currency: p.cash.Currency},
		DailyPnLPct: domain.Percentage{Value: 0},
		SectorExposure:   map[string]domain.Percentage{},
		CurrencyExposure: map[domain.Currency]domain.Percentage{},
	}, nil
}

func (p *Paper) GetOrders(_ context.Context) ([]domain.Order, error) {
	p.mu.RLock()
	defer p.mu.RUnlock()

	result := make([]domain.Order, len(p.orders))
	copy(result, p.orders)
	return result, nil
}

func (p *Paper) resolvePrice(ctx context.Context, symbol string, exchange domain.Exchange, override *float64) (float64, error) {
	if override != nil {
		return *override, nil
	}
	price, err := p.marketData.GetPrice(ctx, symbol, exchange)
	if err != nil {
		return 0, err
	}
	if price == nil {
		return 0, fmt.Errorf("no price available for %s", symbol)
	}
	return price.Current, nil
}

func (p *Paper) positionQty(symbol string) int {
	if pos, ok := p.positions[symbol]; ok {
		return pos.Quantity
	}
	return 0
}
