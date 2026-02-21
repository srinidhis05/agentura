package domain

type GeopoliticalScenario struct {
	ID              string              `json:"id"`
	Name            string              `json:"name"`
	Framework       string              `json:"framework"`
	TriggerWords    []string            `json:"triggerWords"`
	BullishSectors  []string            `json:"bullishSectors"`
	BearishSectors  []string            `json:"bearishSectors"`
	Stocks          map[Market][]string `json:"stocks"`
	CurrencyImpact  map[Currency]float64 `json:"currencyImpact"`
}
