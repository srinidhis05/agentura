package grpc

// AgentServer is a placeholder for the Python → Go callback gRPC server.
// Implements CallbackService: GetMarketData, GetPortfolio, ExecuteTrade, etc.
// Will be generated from proto/agent/v1/agent.proto.

type AgentServer struct {
	// Dependencies will be injected:
	// marketData port.MarketDataPort
	// broker     port.BrokerPort
	// risk       port.RiskPort
	// notifier   port.NotifierPort
}

func NewAgentServer() *AgentServer {
	return &AgentServer{}
}

// TODO: Implement gRPC server methods once proto is compiled:
// - GetMarketData(ctx, MarketDataRequest) → MarketDataResponse
// - GetPortfolio(ctx, PortfolioRequest) → PortfolioResponse
// - ExecuteTrade(ctx, TradeRequest) → TradeResponse
// - ValidateRisk(ctx, RiskRequest) → RiskResponse
// - SendNotification(ctx, NotificationRequest) → NotificationResponse
