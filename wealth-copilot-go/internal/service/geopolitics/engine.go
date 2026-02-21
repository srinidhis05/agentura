package geopolitics

import (
	"strings"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
)

var scenarios = []domain.GeopoliticalScenario{
	{
		ID:             "china-taiwan",
		Name:           "China-Taiwan Tensions",
		Framework:      "prisoners-of-geography",
		TriggerWords:   []string{"taiwan", "china tension", "strait crisis", "chip war", "semiconductor blockade"},
		BullishSectors: []string{"Defense", "Cybersecurity", "Domestic Semiconductor", "Gold"},
		BearishSectors: []string{"Consumer Electronics", "Shipping", "Luxury Goods", "China ADRs"},
		Stocks: map[domain.Market][]string{
			domain.MarketIndia:     {"HAL.NS", "BEL.NS", "HINDPETRO.NS", "ONGC.NS"},
			domain.MarketUS:        {"LMT", "RTX", "NOC", "GD", "PANW", "CRWD"},
			domain.MarketUK:        {"BAE.L", "RR.L"},
			domain.MarketUAE:       {},
			domain.MarketSingapore: {"ST.SI"},
			domain.MarketCrypto:    {"BTC-USD", "ETH-USD"},
		},
		CurrencyImpact: map[domain.Currency]float64{
			domain.CurrencyINR: -0.05, domain.CurrencyUSD: 0.10, domain.CurrencyAED: 0.02,
			domain.CurrencyGBP: -0.03, domain.CurrencyEUR: -0.05, domain.CurrencySGD: -0.08,
			domain.CurrencyCAD: 0.02, domain.CurrencyAUD: -0.10,
		},
	},
	{
		ID:             "russia-nato",
		Name:           "Russia-NATO Escalation",
		Framework:      "grand-chessboard",
		TriggerWords:   []string{"russia", "nato", "ukraine", "european war", "energy crisis"},
		BullishSectors: []string{"Energy", "Defense", "Agriculture", "Gold"},
		BearishSectors: []string{"European Banks", "Travel", "Luxury", "Auto"},
		Stocks: map[domain.Market][]string{
			domain.MarketIndia:     {"ONGC.NS", "RELIANCE.NS", "GAIL.NS", "COALINDIA.NS"},
			domain.MarketUS:        {"XOM", "CVX", "OXY", "LMT", "RTX", "ADM", "GLD"},
			domain.MarketUK:        {"BP.L", "SHEL.L"},
			domain.MarketUAE:       {"ADNOCDIST.AD"},
			domain.MarketSingapore: {},
			domain.MarketCrypto:    {"BTC-USD"},
		},
		CurrencyImpact: map[domain.Currency]float64{
			domain.CurrencyINR: -0.03, domain.CurrencyUSD: 0.15, domain.CurrencyAED: 0.08,
			domain.CurrencyGBP: -0.10, domain.CurrencyEUR: -0.15, domain.CurrencySGD: 0.02,
			domain.CurrencyCAD: 0.05, domain.CurrencyAUD: 0.03,
		},
	},
	{
		ID:             "middle-east",
		Name:           "Middle East Conflict",
		Framework:      "prisoners-of-geography",
		TriggerWords:   []string{"iran", "israel", "saudi", "oil crisis", "strait of hormuz", "opec", "gaza", "hezbollah"},
		BullishSectors: []string{"Oil & Gas", "Defense", "Solar", "Gold"},
		BearishSectors: []string{"Airlines", "Travel", "Consumer Discretionary"},
		Stocks: map[domain.Market][]string{
			domain.MarketIndia:     {"RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS"},
			domain.MarketUS:        {"XOM", "CVX", "SLB", "HAL", "FSLR", "ENPH"},
			domain.MarketUK:        {"BP.L", "SHEL.L"},
			domain.MarketUAE:       {},
			domain.MarketSingapore: {},
			domain.MarketCrypto:    {"BTC-USD", "ETH-USD"},
		},
		CurrencyImpact: map[domain.Currency]float64{
			domain.CurrencyINR: -0.08, domain.CurrencyUSD: 0.10, domain.CurrencyAED: -0.05,
			domain.CurrencyGBP: -0.02, domain.CurrencyEUR: -0.05, domain.CurrencySGD: -0.02,
			domain.CurrencyCAD: 0.08, domain.CurrencyAUD: 0.02,
		},
	},
	{
		ID:             "india-china",
		Name:           "India-China Border Tensions",
		Framework:      "prisoners-of-geography",
		TriggerWords:   []string{"ladakh", "galwan", "india china", "border clash", "lac tension", "arunachal"},
		BullishSectors: []string{"Indian Defense", "Indian IT", "Domestic Manufacturing"},
		BearishSectors: []string{"Chinese Imports", "Electronics"},
		Stocks: map[domain.Market][]string{
			domain.MarketIndia:     {"HAL.NS", "BEL.NS", "BHARATFORG.NS", "TCS.NS", "INFY.NS"},
			domain.MarketUS:        {"LMT", "BA", "GD"},
			domain.MarketUK:        {},
			domain.MarketUAE:       {},
			domain.MarketSingapore: {},
			domain.MarketCrypto:    {},
		},
		CurrencyImpact: map[domain.Currency]float64{
			domain.CurrencyINR: -0.05, domain.CurrencyUSD: 0.05, domain.CurrencyAED: 0.02,
			domain.CurrencyGBP: 0.00, domain.CurrencyEUR: 0.00, domain.CurrencySGD: -0.02,
			domain.CurrencyCAD: 0.00, domain.CurrencyAUD: -0.03,
		},
	},
	{
		ID:             "dollar-dedollarization",
		Name:           "De-dollarization Trend",
		Framework:      "grand-chessboard",
		TriggerWords:   []string{"dedollarization", "brics currency", "dollar collapse", "yuan", "gold standard", "brics"},
		BullishSectors: []string{"Gold", "Commodities", "Crypto", "Emerging Markets"},
		BearishSectors: []string{"US Banks", "US Treasury", "Dollar-denominated Debt"},
		Stocks: map[domain.Market][]string{
			domain.MarketIndia:     {"GOLDBEES.NS", "TITAN.NS", "RELIANCE.NS"},
			domain.MarketUS:        {"GLD", "SLV", "GOLD", "NEM", "FCX"},
			domain.MarketUK:        {"GLEN.L", "RIO.L"},
			domain.MarketUAE:       {},
			domain.MarketSingapore: {},
			domain.MarketCrypto:    {"BTC-USD", "ETH-USD", "XRP-USD"},
		},
		CurrencyImpact: map[domain.Currency]float64{
			domain.CurrencyINR: 0.05, domain.CurrencyUSD: -0.15, domain.CurrencyAED: 0.08,
			domain.CurrencyGBP: 0.02, domain.CurrencyEUR: 0.05, domain.CurrencySGD: 0.03,
			domain.CurrencyCAD: 0.03, domain.CurrencyAUD: 0.05,
		},
	},
	{
		ID:             "climate-energy",
		Name:           "Climate/Energy Transition",
		Framework:      "prisoners-of-geography",
		TriggerWords:   []string{"climate", "renewable", "ev transition", "carbon tax", "green energy", "net zero", "cop28"},
		BullishSectors: []string{"Solar", "EV", "Battery", "Green Hydrogen"},
		BearishSectors: []string{"Coal", "Traditional Oil", "Legacy Auto"},
		Stocks: map[domain.Market][]string{
			domain.MarketIndia:     {"TATAPOWER.NS", "ADANIGREEN.NS", "SUZLON.NS", "TATAMOTORS.NS"},
			domain.MarketUS:        {"TSLA", "RIVN", "FSLR", "ENPH", "PLUG", "NEE"},
			domain.MarketUK:        {"SSE.L", "NG.L"},
			domain.MarketUAE:       {"MASDAR"},
			domain.MarketSingapore: {},
			domain.MarketCrypto:    {},
		},
		CurrencyImpact: map[domain.Currency]float64{
			domain.CurrencyINR: 0.00, domain.CurrencyUSD: -0.02, domain.CurrencyAED: -0.05,
			domain.CurrencyGBP: 0.02, domain.CurrencyEUR: 0.03, domain.CurrencySGD: 0.02,
			domain.CurrencyCAD: -0.03, domain.CurrencyAUD: 0.05,
		},
	},
	{
		ID:             "fed-rate-cycle",
		Name:           "Fed Rate Pivot",
		Framework:      "macro-economics",
		TriggerWords:   []string{"fed rate", "interest rate", "jerome powell", "rate cut", "rate hike", "fomc"},
		BullishSectors: []string{"Growth Tech", "Real Estate", "High-Dividend"},
		BearishSectors: []string{"Banks", "Insurance"},
		Stocks: map[domain.Market][]string{
			domain.MarketIndia:     {"HDFC.NS", "ICICIBANK.NS", "SBIN.NS"},
			domain.MarketUS:        {"QQQ", "VNQ", "XLU", "MSFT", "GOOGL"},
			domain.MarketUK:        {"LAND.L"},
			domain.MarketUAE:       {},
			domain.MarketSingapore: {"C31.SI", "D05.SI"},
			domain.MarketCrypto:    {"BTC-USD", "ETH-USD"},
		},
		CurrencyImpact: map[domain.Currency]float64{
			domain.CurrencyINR: 0.05, domain.CurrencyUSD: -0.08, domain.CurrencyAED: 0.00,
			domain.CurrencyGBP: 0.03, domain.CurrencyEUR: 0.03, domain.CurrencySGD: 0.02,
			domain.CurrencyCAD: 0.02, domain.CurrencyAUD: 0.03,
		},
	},
}

type Engine struct{}

func NewEngine() *Engine {
	return &Engine{}
}

func (e *Engine) GetScenarios() []domain.GeopoliticalScenario {
	return scenarios
}

func (e *Engine) DetectScenario(input string) *domain.GeopoliticalScenario {
	lower := strings.ToLower(input)
	for i := range scenarios {
		for _, trigger := range scenarios[i].TriggerWords {
			if strings.Contains(lower, trigger) {
				return &scenarios[i]
			}
		}
	}
	return nil
}

func (e *Engine) GetStocksForScenario(scenarioID string, markets []domain.Market) []string {
	for _, s := range scenarios {
		if s.ID == scenarioID {
			var stocks []string
			for _, m := range markets {
				stocks = append(stocks, s.Stocks[m]...)
			}
			return stocks
		}
	}
	return nil
}

func (e *Engine) GetCurrencyImpact(scenarioID string) map[domain.Currency]float64 {
	for _, s := range scenarios {
		if s.ID == scenarioID {
			return s.CurrencyImpact
		}
	}
	return nil
}

// DetectActiveScenarios detects multiple scenarios from news items.
func DetectActiveScenarios(newsItems []string) []domain.GeopoliticalScenario {
	engine := NewEngine()
	detected := make(map[string]bool)
	var result []domain.GeopoliticalScenario

	for _, news := range newsItems {
		s := engine.DetectScenario(news)
		if s != nil && !detected[s.ID] {
			detected[s.ID] = true
			result = append(result, *s)
		}
	}
	return result
}

// CalculateNetCurrencyImpact computes the average currency impact across active scenarios.
func CalculateNetCurrencyImpact(active []domain.GeopoliticalScenario) map[domain.Currency]float64 {
	impact := make(map[domain.Currency]float64)
	for _, c := range domain.AllCurrencies {
		impact[c] = 0
	}

	for _, s := range active {
		for c, delta := range s.CurrencyImpact {
			impact[c] += delta
		}
	}

	if len(active) > 1 {
		for c := range impact {
			impact[c] /= float64(len(active))
		}
	}
	return impact
}
