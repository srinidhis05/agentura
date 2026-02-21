package marketdata

import (
	"context"
	"time"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

// Mock implements MarketDataPort with realistic demo data.
type Mock struct {
	prices map[string]domain.Price
}

func NewMock() *Mock {
	now := time.Now()
	return &Mock{
		prices: map[string]domain.Price{
			"RELIANCE.NS": {Symbol: "RELIANCE.NS", Exchange: domain.ExchangeNSE, Current: 2450.50, Open: 2430.00, High: 2465.00, Low: 2425.00, Volume: 5_200_000, Change: domain.Percentage{Value: 0.84}, Currency: domain.CurrencyINR, Timestamp: now},
			"TCS.NS":      {Symbol: "TCS.NS", Exchange: domain.ExchangeNSE, Current: 3850.25, Open: 3820.00, High: 3870.00, Low: 3810.00, Volume: 1_800_000, Change: domain.Percentage{Value: 0.79}, Currency: domain.CurrencyINR, Timestamp: now},
			"INFY.NS":     {Symbol: "INFY.NS", Exchange: domain.ExchangeNSE, Current: 1580.75, Open: 1565.00, High: 1590.00, Low: 1560.00, Volume: 3_100_000, Change: domain.Percentage{Value: 1.01}, Currency: domain.CurrencyINR, Timestamp: now},
			"AAPL":        {Symbol: "AAPL", Exchange: domain.ExchangeNASDAQ, Current: 185.50, Open: 184.00, High: 186.20, Low: 183.50, Volume: 45_000_000, Change: domain.Percentage{Value: 0.81}, Currency: domain.CurrencyUSD, Timestamp: now},
			"MSFT":        {Symbol: "MSFT", Exchange: domain.ExchangeNASDAQ, Current: 415.30, Open: 413.00, High: 417.00, Low: 412.00, Volume: 22_000_000, Change: domain.Percentage{Value: 0.56}, Currency: domain.CurrencyUSD, Timestamp: now},
			"BTC-USD":     {Symbol: "BTC-USD", Exchange: domain.ExchangeCRYPTO, Current: 97500.00, Open: 96800.00, High: 98200.00, Low: 96500.00, Volume: 28_000_000_000, Change: domain.Percentage{Value: 0.72}, Currency: domain.CurrencyUSD, Timestamp: now},
		},
	}
}

func (m *Mock) GetPrice(_ context.Context, symbol string, _ domain.Exchange) (*domain.Price, error) {
	if p, ok := m.prices[symbol]; ok {
		return &p, nil
	}
	return nil, nil
}

func (m *Mock) GetPrices(_ context.Context, symbols []string) (map[string]domain.Price, error) {
	result := make(map[string]domain.Price)
	for _, s := range symbols {
		if p, ok := m.prices[s]; ok {
			result[s] = p
		}
	}
	return result, nil
}

func (m *Mock) GetFundamentals(_ context.Context, symbol string) (*domain.Fundamentals, error) {
	pe := 22.5
	pb := 3.2
	div := domain.Percentage{Value: 1.5}
	roe := domain.Percentage{Value: 18.5}
	margin := domain.Percentage{Value: 12.3}
	de := 0.85
	beta := 1.1
	sector := "Technology"
	industry := "Software"

	return &domain.Fundamentals{
		Symbol:        symbol,
		PERatio:       &pe,
		PBRatio:       &pb,
		DividendYield: &div,
		ROE:           &roe,
		ProfitMargin:  &margin,
		DebtToEquity:  &de,
		Beta:          &beta,
		Sector:        &sector,
		Industry:      &industry,
	}, nil
}

func (m *Mock) GetTechnicals(_ context.Context, symbol string, _ string) (*domain.Technicals, error) {
	sma50 := 180.0
	sma200 := 170.0
	return &domain.Technicals{
		Symbol:        symbol,
		RSI:           55.0,
		RSISignal:     domain.RSISignalNeutral,
		MACD:          1.2,
		MACDSignal:    0.8,
		MACDHistogram: 0.4,
		MACDTrend:     domain.MACDTrendBullish,
		SMA20:         185.0,
		SMA50:         &sma50,
		SMA200:        &sma200,
		Trend:         domain.TrendUptrend,
		BBUpper:       190.0,
		BBLower:       180.0,
		BBPercentB:    0.65,
	}, nil
}
