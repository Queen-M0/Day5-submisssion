from app.providers.mock_ai_provider import MockAIProvider
from app.services.context_service import ContextService
from app.services.moderation_service import ModerationService


moderation_service = ModerationService(MockAIProvider(), ContextService())

