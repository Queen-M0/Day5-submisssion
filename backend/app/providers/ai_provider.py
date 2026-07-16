from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

from app.schemas.common import ModerationResult


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
    messages: List[ContextMessage] = field(default_factory=list)


class ModerationProvider(ABC):
    name = "abstract"

    @abstractmethod
    def moderate(self, payload: ModerationInput) -> ModerationResult:
        raise NotImplementedError

