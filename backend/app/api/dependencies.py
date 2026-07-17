from app.core.config import get_settings
from app.providers.mimo_provider import MiMoProvider
from app.providers.mock_ai_provider import MockAIProvider
from app.services.appeal_service import AppealService
from app.services.context_service import ContextService
from app.services.moderation_service import ModerationService


settings = get_settings()
if settings.ai_provider == "mimo" or (settings.ai_provider == "auto" and settings.mimo_api_key):
    provider = MiMoProvider(
        api_key=settings.mimo_api_key,
        base_url=settings.mimo_base_url,
        model=settings.mimo_model,
        timeout_seconds=settings.mimo_timeout_seconds,
        max_tokens=settings.mimo_max_tokens,
        temperature=settings.mimo_temperature,
        json_mode=settings.mimo_json_mode,
    )
else:
    provider = MockAIProvider()

secondary_provider = None
if settings.ai_dual_review_enabled:
    if settings.ai_provider == "mimo" or (settings.ai_provider == "auto" and settings.mimo_api_key):
        secondary_provider = MiMoProvider(
            api_key=settings.mimo_api_key,
            base_url=settings.mimo_base_url,
            model=settings.mimo_secondary_model,
            timeout_seconds=settings.mimo_timeout_seconds,
            max_tokens=settings.mimo_max_tokens,
            temperature=settings.mimo_temperature,
            json_mode=settings.mimo_json_mode,
        )
    else:
        secondary_provider = MockAIProvider()

context_service = ContextService()
moderation_service = ModerationService(provider, context_service, secondary_provider)
appeal_service = AppealService(provider, context_service)

