import logging

from app.core.config import get_settings
from app.providers.ai_provider import ModerationProvider
from app.providers.mock_ai_provider import MockAIProvider
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
