from app.providers.factory import get_moderation_provider
from app.services.context_service import ContextService
from app.services.moderation_service import ModerationService


moderation_service = ModerationService(get_moderation_provider(), ContextService())
