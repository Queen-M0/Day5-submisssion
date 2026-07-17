from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.schemas.common import CounterAnalysisResult, ModerationResult


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
    model_version = "unknown"
    moderation_prompt_version = "moderation-v1"
    appeal_prompt_version = "appeal-critic-v1"

    @abstractmethod
    def moderate(self, payload: ModerationInput) -> ModerationResult:
        raise NotImplementedError

    @abstractmethod
    def analyze_appeal(self, payload: AppealInput) -> CounterAnalysisResult:
        raise NotImplementedError
