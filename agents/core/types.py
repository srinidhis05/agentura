"""Core domain types for agent system.

These types bridge the TypeScript domain layer (packages/core/domain/types.ts)
with the Python agent runtime.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    INR = "INR"
    AED = "AED"
    SGD = "SGD"
    GBP = "GBP"
    EUR = "EUR"


class GoalType(str, Enum):
    """Financial goal types"""
    HOUSE = "house_deposit"
    EDUCATION = "education_fund"
    RETIREMENT = "retirement"
    EMERGENCY = "emergency_fund"
    CUSTOM = "custom"


class RiskTolerance(str, Enum):
    """User risk tolerance levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class Money(BaseModel):
    """Currency-aware money type"""
    amount: Decimal = Field(ge=0)
    currency: Currency


class UserMessage(BaseModel):
    """Incoming message from user"""
    user_id: str
    message: str
    channel: Literal["slack", "whatsapp", "web"]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None


class ConversationContext(BaseModel):
    """Context for agent decision-making"""
    user_id: str
    session_id: str
    location: str  # e.g., "Dubai, UAE"
    primary_currency: Currency
    risk_tolerance: Optional[RiskTolerance] = None
    active_goals: list[str] = Field(default_factory=list)
    conversation_history: list[dict] = Field(default_factory=list, max_length=10)


class AgentAction(BaseModel):
    """Actions the agent can take"""
    type: Literal[
        "respond",
        "execute_skill",
        "request_approval",
        "trigger_workflow"
    ]
    payload: dict
    reasoning: str


class Goal(BaseModel):
    """Financial goal definition"""
    id: str
    user_id: str
    type: GoalType
    name: str
    target_amount: Money
    target_date: datetime
    current_amount: Money
    priority: int = Field(ge=1, le=5)
    created_at: datetime = Field(default_factory=datetime.utcnow)
