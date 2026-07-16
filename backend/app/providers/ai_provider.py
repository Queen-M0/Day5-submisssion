from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.schemas.common import AppealCriticResult, ModerationResult


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


class ModerationProvider(ABC):
    name = "abstract"
    prompt_version = "unknown"
    model_version = "unknown"
    rule_version = "unknown"

    @abstractmethod
    def moderate(self, payload: ModerationInput) -> ModerationResult:
        raise NotImplementedError


@dataclass
class AppealContext:
    """The initial moderation verdict that the appeal critic MUST consume.

    It is reconstructed from the persisted ModerationRecord so the re-review is
    time-decoupled from the first review and cannot silently drift.
    """

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
    prompt_version = "unknown"
    model_version = "unknown"
    rule_version = "unknown"

    @abstractmethod
    def critique(self, payload: AppealCriticInput) -> AppealCriticResult:
        raise NotImplementedError
