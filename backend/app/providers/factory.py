import logging
from typing import Optional

from app.core.config import get_settings
from app.providers.ai_provider import AppealCriticProvider, ModerationProvider
from app.providers.mimo_provider import MiMoProvider
from app.providers.mock_ai_provider import MockAIProvider
from app.providers.mock_appeal_critic_provider import MockAppealCriticProvider
from app.providers.real_appeal_critic_provider import RealAppealCriticProvider

logger = logging.getLogger(__name__)


def _real_key(settings) -> str:
    return settings.mimo_api_key or settings.ai_api_key


def _real_base_url(settings) -> str:
    return settings.mimo_base_url or settings.ai_base_url


def _use_real_provider(settings) -> bool:
    mode = settings.ai_provider.lower()
    if mode in {"mimo", "real"}:
        return True
    return mode == "auto" and bool(_real_key(settings))


def _mimo_provider(model: str) -> MiMoProvider:
    settings = get_settings()
    return MiMoProvider(
        api_key=_real_key(settings),
        base_url=_real_base_url(settings),
        model=model,
        timeout_seconds=settings.mimo_timeout_seconds,
        max_tokens=settings.mimo_max_tokens,
        temperature=settings.mimo_temperature,
        json_mode=settings.mimo_json_mode,
    )


def get_moderation_provider() -> ModerationProvider:
    settings = get_settings()
    if _use_real_provider(settings):
        if not _real_key(settings):
            logger.warning("AI_PROVIDER=%s but no API key is configured; falling back to MockAIProvider", settings.ai_provider)
            return MockAIProvider()
        model = settings.mimo_model or settings.ai_model
        logger.info("Using MiMo moderation provider model=%s", model)
        return _mimo_provider(model)
    return MockAIProvider()


def get_secondary_moderation_provider() -> Optional[ModerationProvider]:
    settings = get_settings()
    if not settings.ai_dual_review_enabled:
        return None
    if _use_real_provider(settings):
        if not _real_key(settings):
            logger.warning("Dual review requested without API key; using mock secondary provider")
            return MockAIProvider()
        model = settings.mimo_secondary_model or settings.mimo_model or settings.ai_model
        logger.info("Using MiMo secondary moderation provider model=%s", model)
        return _mimo_provider(model)
    return MockAIProvider()


def get_appeal_critic_provider() -> AppealCriticProvider:
    """Build the appeal re-review provider.

    We keep appeal critique as a separate provider boundary so the initial
    moderation agent and the appeal critic can evolve independently.
    """
    settings = get_settings()
    if _use_real_provider(settings):
        if not _real_key(settings):
            logger.warning("AI_PROVIDER=%s but no API key is configured; falling back to MockAppealCriticProvider", settings.ai_provider)
            return MockAppealCriticProvider()
        model = settings.ai_appeal_model or settings.mimo_model or settings.ai_model
        logger.info("Using real appeal critic provider model=%s", model)
        return RealAppealCriticProvider(
            api_key=_real_key(settings),
            base_url=_real_base_url(settings),
            model=model,
            prompt_version=settings.ai_appeal_prompt_version,
            rule_version=settings.ai_appeal_rule_version,
            timeout=settings.ai_timeout,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
        )
    return MockAppealCriticProvider()
