package grpc

// AgentClient is a placeholder for the Go → Python gRPC client.
// Implements: Chat, AnalyzeStock, RebalanceRecommendation.
// Will be generated from proto/agent/v1/agent.proto.

type AgentClient struct {
	addr string
}

func NewAgentClient(addr string) *AgentClient {
	return &AgentClient{addr: addr}
}

// TODO: Implement gRPC client methods once proto is compiled:
// - Chat(ctx, ChatRequest) → stream ChatResponse
// - AnalyzeStock(ctx, AnalyzeStockRequest) → AnalyzeStockResponse
// - RebalanceRecommendation(ctx, RebalanceRequest) → RebalanceResponse
