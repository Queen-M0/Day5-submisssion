import logging

from app.core.config import get_settings
from app.providers.ai_provider import AppealCriticProvider, ModerationProvider
from app.providers.mock_ai_provider import MockAIProvider
from app.providers.mock_appeal_critic_provider import MockAppealCriticProvider
from app.providers.real_appeal_critic_provider import RealAppealCriticProvider
from app.providers.real_moderation_provider import RealModerationProvider

logger = logging.getLogger(__name__)


def get_moderation_provider() -> ModerationProvider:
    settings = get_settings()
    if settings.ai_provider.lower() == "real":
        if not settings.ai_api_key:
            logger.warning("AI_PROVIDER=real but AI_API_KEY is empty; falling back to MockAIProvider")
            return MockAIProvider()
        logger.info("Using RealModerationProvider model=%s", settings.ai_model)
        return RealModerationProvider(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            model=settings.ai_model,
            prompt_version=settings.ai_prompt_version,
            rule_version=settings.ai_rule_version,
            timeout=settings.ai_timeout,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
        )
    return MockAIProvider()


def get_appeal_critic_provider() -> AppealCriticProvider:
    """Build the appeal re-review ("counter-argument") provider.

    Reuses the same API key/model as the moderation provider. When the real
    API is unavailable or not configured, falls back to a deterministic mock so
    the appeal flow still produces a usable counter_analysis offline.
    """
    settings = get_settings()
    if settings.ai_provider.lower() == "real":
        if not settings.ai_api_key:
            logger.warning("AI_PROVIDER=real but AI_API_KEY is empty; falling back to MockAppealCriticProvider")
            return MockAppealCriticProvider()
        logger.info("Using RealAppealCriticProvider model=%s", settings.ai_model)
        return RealAppealCriticProvider(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            model=settings.ai_appeal_model or settings.ai_model,
            prompt_version=settings.ai_appeal_prompt_version,
            rule_version=settings.ai_appeal_rule_version,
            timeout=settings.ai_timeout,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
        )
    return MockAppealCriticProvider()
