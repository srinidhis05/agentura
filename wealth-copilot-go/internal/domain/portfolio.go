package domain

import "time"

type Position struct {
	Symbol       string     `json:"symbol"`
	Exchange     Exchange   `json:"exchange"`
	Quantity     int        `json:"quantity"`
	AvgPrice     float64    `json:"avgPrice"`
	CurrentPrice float64    `json:"currentPrice"`
	PnL          Money      `json:"pnl"`
	PnLPct       Percentage `json:"pnlPct"`
	StopLoss     *float64   `json:"stopLoss,omitempty"`
	Currency     Currency   `json:"currency"`
}

type Portfolio struct {
	Cash             Money                   `json:"cash"`
	Positions        []Position              `json:"positions"`
	TotalValue       Money                   `json:"totalValue"`
	DailyPnL         Money                   `json:"dailyPnl"`
	DailyPnLPct      Percentage              `json:"dailyPnlPct"`
	SectorExposure   map[string]Percentage   `json:"sectorExposure"`
	CurrencyExposure map[Currency]Percentage `json:"currencyExposure"`
}

type OrderStatus string

const (
	OrderStatusPending   OrderStatus = "PENDING"
	OrderStatusFilled    OrderStatus = "FILLED"
	OrderStatusRejected  OrderStatus = "REJECTED"
	OrderStatusCancelled OrderStatus = "CANCELLED"
)

type Broker string

const (
	BrokerPaper   Broker = "paper"
	BrokerZerodha Broker = "zerodha"
	BrokerGroww   Broker = "groww"
	BrokerAlpaca  Broker = "alpaca"
	BrokerIBKR    Broker = "ibkr"
)

type OrderType string

const (
	OrderTypeMarket OrderType = "MARKET"
	OrderTypeLimit  OrderType = "LIMIT"
)

type Order struct {
	ID        string      `json:"id"`
	Timestamp time.Time   `json:"timestamp"`
	Action    Action      `json:"action"`
	Symbol    string      `json:"symbol"`
	Exchange  Exchange    `json:"exchange"`
	Quantity  int         `json:"quantity"`
	Price     float64     `json:"price"`
	Status    OrderStatus `json:"status"`
	Broker    Broker      `json:"broker"`
	Currency  Currency    `json:"currency"`
}

type OrderRequest struct {
	Symbol    string    `json:"symbol"`
	Exchange  Exchange  `json:"exchange"`
	Quantity  int       `json:"quantity"`
	OrderType OrderType `json:"orderType"`
	Price     *float64  `json:"price,omitempty"`
}

type Transaction struct {
	ID        string    `json:"id"`
	Action    Action    `json:"action"`
	Symbol    string    `json:"symbol"`
	Exchange  Exchange  `json:"exchange"`
	Quantity  int       `json:"quantity"`
	Price     float64   `json:"price"`
	Currency  Currency  `json:"currency"`
	Timestamp time.Time `json:"timestamp"`
}
