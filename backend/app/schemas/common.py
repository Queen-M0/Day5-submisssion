from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class APIModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class UserSummary(APIModel):
    id: str
    username: str
    display_name: str
    role: str


class EvidenceItem(APIModel):
    text: str
    reason: str
    risk_type: str
    content_id: Optional[str] = None


class ModerationResult(APIModel):
    is_violation: bool
    risk_level: int = Field(ge=0, le=3)
    risk_score: int = Field(ge=0, le=100)
    risk_types: List[str]
    confidence: float = Field(ge=0, le=1)
    decision: str
    target_users: List[str] = Field(default_factory=list)
    is_quote_or_report: bool = False
    quote_context_safe: bool = False
    has_implicit_attack: bool = False
    has_continuous_harassment: bool = False
    evidence: List[EvidenceItem] = Field(default_factory=list)
    context_reasoning: str
    user_visible_reason: str
    reviewer_reason: str
    suggested_revision: str = ""


class AppealCriticResult(APIModel):
    """Output of the appeal re-review ("counter-argument") agent.

    The agent does NOT make the final decision; it actively challenges the
    first review and gives a human reviewer two-sided arguments plus a
    non-binding recommendation. Field names are camelCased to match the
    frontend CounterAnalysis contract (supportsOriginalDecision /
    supportsChange / newEvidenceImpact / remainingUncertainties /
    reviewSuggestion).
    """

    upholds_initial: bool
    recommended_decision: str
    confidence: float = Field(ge=0, le=1)
    risk_level: int = Field(ge=0, le=3)
    risk_score: int = Field(ge=0, le=100)
    risk_types: List[str] = Field(default_factory=list)
    supports_original_decision: List[str] = Field(default_factory=list)
    supports_change: List[str] = Field(default_factory=list)
    new_evidence_impact: str
    remaining_uncertainties: List[str] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    review_suggestion: str
    reasoning: str


class ContentItem(APIModel):
    id: str
    scene_id: str
    content_type: str
    author: UserSummary
    parent_id: Optional[str]
    parent_author_name: Optional[str] = None
    text: str
    status: str
    visible_to_public: bool
    created_at: datetime
    moderation: Optional[Dict[str, Any]] = None

