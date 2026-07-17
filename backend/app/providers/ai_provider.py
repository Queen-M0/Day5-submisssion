from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.schemas.common import AppealCriticResult, CounterAnalysisResult, ModerationResult


@dataclass
class ContextMessage:
    id: str
    author_id: str
    author_name: str
    text: str
    parent_id: Optional[str]


@dataclass
class ModerationInput:
    content_id: str
    author_id: str
    author_name: str
    text: str
    parent_text: Optional[str]
    topic_title: str = ""
    parent_id: Optional[str] = None
    parent_author_id: Optional[str] = None
    messages: List[ContextMessage] = field(default_factory=list)
    author_history: List[ContextMessage] = field(default_factory=list)
    target_history: List[ContextMessage] = field(default_factory=list)


@dataclass
class AppealInput:
    appeal_id: str
    content: ModerationInput
    appeal_type: str
    reason: str
    extra_context: str
    original_moderation: Dict[str, Any]


class ModerationProvider(ABC):
    name = "abstract"
    prompt_version = "moderation-v1"
    moderation_prompt_version = "moderation-v1"
    appeal_prompt_version = "appeal-critic-v1"
    model_version = "unknown"
    rule_version = "unknown"

    @abstractmethod
    def moderate(self, payload: ModerationInput) -> ModerationResult:
        raise NotImplementedError

    def analyze_appeal(self, payload: AppealInput) -> CounterAnalysisResult:
        raise NotImplementedError


@dataclass
class AppealContext:
    """Persisted initial moderation verdict consumed by the appeal critic."""

    review_id: str
    decision: str
    system_decision: str
    risk_level: int
    risk_score: int
    risk_types: List[str]
    confidence: float
    user_visible_reason: str
    reviewer_reason: str
    evidence: List[Dict[str, Any]]


@dataclass
class AppealCriticInput:
    content_id: str
    author_id: str
    author_name: str
    text: str
    topic_title: str
    appeal_type: str
    appeal_reason: str
    extra_context: str
    initial_review: AppealContext
    parent_text: Optional[str] = None
    parent_id: Optional[str] = None
    parent_author_id: Optional[str] = None
    context_messages: List[ContextMessage] = field(default_factory=list)


class AppealCriticProvider(ABC):
    name = "abstract"
    prompt_version = "appeal-critic-v1"
    appeal_prompt_version = "appeal-critic-v1"
    model_version = "unknown"
    rule_version = "unknown"

    @abstractmethod
    def critique(self, payload: AppealCriticInput) -> AppealCriticResult:
        raise NotImplementedError
