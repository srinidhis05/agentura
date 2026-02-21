package port

import "github.com/wealth-copilot/wealth-copilot-go/internal/domain"

type GeopoliticsPort interface {
	GetScenarios() []domain.GeopoliticalScenario
	DetectScenario(input string) *domain.GeopoliticalScenario
	GetStocksForScenario(scenarioID string, markets []domain.Market) []string
	GetCurrencyImpact(scenarioID string) map[domain.Currency]float64
}
