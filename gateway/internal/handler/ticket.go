package handler

import (
	"fmt"
	"io"
	"net/http"

	"github.com/agentura-ai/agentura/gateway/internal/adapter/executor"
	"github.com/agentura-ai/agentura/gateway/pkg/httputil"
)

// TicketHandler proxies ticket requests to the Python executor.
type TicketHandler struct {
	executor *executor.Client
}

// NewTicketHandler creates a handler for ticket endpoints.
func NewTicketHandler(exec *executor.Client) *TicketHandler {
	return &TicketHandler{executor: exec}
}

// ListTickets proxies GET /api/v1/tickets to the executor.
func (h *TicketHandler) ListTickets(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ProxyGet(r.Context(), "/api/v1/tickets", r.URL.RawQuery)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// GetTicketStats proxies GET /api/v1/tickets/stats to the executor.
func (h *TicketHandler) GetTicketStats(w http.ResponseWriter, r *http.Request) {
	raw, err := h.executor.ProxyGet(r.Context(), "/api/v1/tickets/stats", r.URL.RawQuery)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// GetTicket proxies GET /api/v1/tickets/{ticket_id} to the executor.
func (h *TicketHandler) GetTicket(w http.ResponseWriter, r *http.Request) {
	ticketID := r.PathValue("ticket_id")
	raw, err := h.executor.ProxyGet(r.Context(), fmt.Sprintf("/api/v1/tickets/%s", ticketID), "")
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// CreateTicket proxies POST /api/v1/tickets to the executor.
func (h *TicketHandler) CreateTicket(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}
	raw, err := h.executor.PostRaw(r.Context(), "/api/v1/tickets", body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	w.Write(raw)
}

// UpdateTicket proxies PUT /api/v1/tickets/{ticket_id} to the executor.
func (h *TicketHandler) UpdateTicket(w http.ResponseWriter, r *http.Request) {
	ticketID := r.PathValue("ticket_id")
	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}
	raw, err := h.executor.PutRaw(r.Context(), fmt.Sprintf("/api/v1/tickets/%s", ticketID), body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// AddTrace proxies POST /api/v1/tickets/{ticket_id}/trace to the executor.
func (h *TicketHandler) AddTrace(w http.ResponseWriter, r *http.Request) {
	ticketID := r.PathValue("ticket_id")
	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}
	raw, err := h.executor.PostRaw(r.Context(), fmt.Sprintf("/api/v1/tickets/%s/trace", ticketID), body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// CheckoutTicket proxies POST /api/v1/tickets/checkout to the executor.
func (h *TicketHandler) CheckoutTicket(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}
	raw, err := h.executor.PostRaw(r.Context(), "/api/v1/tickets/checkout", body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}

// ReleaseTicket proxies POST /api/v1/tickets/{ticket_id}/release to the executor.
func (h *TicketHandler) ReleaseTicket(w http.ResponseWriter, r *http.Request) {
	ticketID := r.PathValue("ticket_id")
	body, err := io.ReadAll(r.Body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadRequest, "failed to read request body")
		return
	}
	raw, err := h.executor.PostRaw(r.Context(), fmt.Sprintf("/api/v1/tickets/%s/release", ticketID), body)
	if err != nil {
		httputil.RespondError(w, http.StatusBadGateway, err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(raw)
}
