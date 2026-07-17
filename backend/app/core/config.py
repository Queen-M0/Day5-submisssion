from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ContextGuard API"
    app_env: str = "development"
    auth_secret: str = "contextguard-development-secret-change-me"
    auth_token_hours: int = 12
    database_url: str = "sqlite:///./contextguard.db"
    frontend_origins: str = "http://localhost:5173"

    # AI provider modes:
    # - mock: deterministic offline provider
    # - mimo: require MiMo/OpenAI-compatible credentials
    # - real: legacy alias for mimo
    # - auto: use real MiMo when a key exists, otherwise mock
    ai_provider: str = "auto"
    mimo_api_key: str = ""
    mimo_base_url: str = "https://api.xiaomimimo.com/v1"
    mimo_model: str = "mimo-v2.5"
    mimo_secondary_model: str = "mimo-v2.5-pro"
    ai_dual_review_enabled: bool = False
    mimo_timeout_seconds: float = 30.0
    mimo_max_tokens: int = 400
    mimo_temperature: float = 0.1
    mimo_json_mode: bool = True

    # Backward-compatible names from the earlier local branch.
    ai_api_key: str = ""
    ai_base_url: str = "https://api.xiaomimimo.com/v1"
    ai_model: str = "mimo-v2.5"
    ai_prompt_version: str = "moderation-v2"
    ai_rule_version: str = "community-v1"
    ai_timeout: float = 12.0
    ai_temperature: float = 0.0
    ai_max_tokens: int = 900

    # Appeal re-review ("counter-argument") agent. Reuses the same API key,
    # base URL, model, timeout, temperature and max_tokens as the moderation
    # provider; only the prompt/rule identity and an optional dedicated model
    # differ so the two agents stay independently versioned.
    ai_appeal_model: str = ""
    ai_appeal_prompt_version: str = "appeal-critic-v1"
    ai_appeal_rule_version: str = "appeal-community-v1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def frontend_origin_list(self):
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
