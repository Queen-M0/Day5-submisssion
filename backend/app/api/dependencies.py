from app.providers.factory import (
    get_appeal_critic_provider,
    get_moderation_provider,
    get_secondary_moderation_provider,
)
from app.services.appeal_service import AppealService
from app.services.context_service import ContextService
from app.services.moderation_service import ModerationService


context_service = ContextService()
moderation_service = ModerationService(
    get_moderation_provider(),
    context_service,
    get_secondary_moderation_provider(),
)
appeal_service = AppealService(get_appeal_critic_provider(), context_service)
