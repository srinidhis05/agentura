package handler

import (
	"net/http"

	"github.com/wealth-copilot/wealth-copilot-go/internal/domain"
	"github.com/wealth-copilot/wealth-copilot-go/internal/middleware"
	"github.com/wealth-copilot/wealth-copilot-go/internal/port"
	"github.com/wealth-copilot/wealth-copilot-go/pkg/httputil"
)

type GoalHandler struct {
	goals port.GoalsPort
}

func NewGoalHandler(g port.GoalsPort) *GoalHandler {
	return &GoalHandler{goals: g}
}

func (h *GoalHandler) Create(w http.ResponseWriter, r *http.Request) {
	var goal domain.Goal
	if err := httputil.DecodeJSON(r, &goal); err != nil {
		httputil.RespondError(w, http.StatusBadRequest, err.Error())
		return
	}

	created, err := h.goals.CreateGoal(r.Context(), goal)
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	httputil.RespondJSON(w, http.StatusCreated, created)
}

func (h *GoalHandler) List(w http.ResponseWriter, r *http.Request) {
	userID := middleware.GetUserID(r.Context())
	goals, err := h.goals.GetAllGoals(r.Context(), userID)
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	httputil.RespondJSON(w, http.StatusOK, goals)
}

func (h *GoalHandler) Get(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	goal, err := h.goals.GetGoal(r.Context(), id)
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	if goal == nil {
		httputil.RespondError(w, http.StatusNotFound, "goal not found")
		return
	}
	httputil.RespondJSON(w, http.StatusOK, goal)
}

func (h *GoalHandler) SuggestAllocation(w http.ResponseWriter, r *http.Request) {
	var req domain.AllocationRequest
	if err := httputil.DecodeJSON(r, &req); err != nil {
		httputil.RespondError(w, http.StatusBadRequest, err.Error())
		return
	}

	allocations, err := h.goals.SuggestAllocation(r.Context(), req)
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	httputil.RespondJSON(w, http.StatusOK, allocations)
}

func (h *GoalHandler) Rebalance(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	signals, err := h.goals.RebalanceGoal(r.Context(), id)
	if err != nil {
		httputil.RespondError(w, http.StatusInternalServerError, err.Error())
		return
	}
	httputil.RespondJSON(w, http.StatusOK, signals)
}
