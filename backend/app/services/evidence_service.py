from typing import Dict, Iterable, List, Tuple

from app.providers.ai_provider import AppealInput, ModerationInput
from app.schemas.common import EvidenceItem


def moderation_sources(payload: ModerationInput) -> Dict[str, str]:
    sources = {payload.content_id: payload.text}
    if payload.parent_id and payload.parent_text:
        sources[payload.parent_id] = payload.parent_text
    for message in [*payload.messages, *payload.author_history, *payload.target_history]:
        sources[message.id] = message.text
    return sources


def appeal_sources(payload: AppealInput) -> Dict[str, str]:
    sources = moderation_sources(payload.content)
    sources["appeal-reason"] = payload.reason
    sources["appeal-extra-context"] = payload.extra_context
    return sources


def validate_evidence(
    evidence: Iterable[EvidenceItem],
    sources: Dict[str, str],
    default_content_id: str,
) -> Tuple[List[dict], bool]:
    items: List[dict] = []
    for item in evidence:
        content_id = item.content_id or default_content_id
        source_text = sources.get(content_id, "")
        verified = bool(item.text.strip()) and item.text in source_text
        items.append(
            {
                "contentId": content_id,
                "quote": item.text,
                "reason": item.reason,
                "riskType": item.risk_type,
                "verified": verified,
            }
        )
    return items, all(item["verified"] for item in items)
