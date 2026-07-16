from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ContextGuard API"
    app_env: str = "development"
    database_url: str = "sqlite:///./contextguard.db"
    frontend_origins: str = "http://localhost:5173"

    ai_provider: str = "mock"
    ai_api_key: str = ""
    ai_base_url: str = "https://api.xiaomimimo.com/v1"
    ai_model: str = "mimo-v2.5"
    ai_prompt_version: str = "moderation-v1"
    ai_rule_version: str = "community-v1"
    ai_timeout: float = 12.0
    ai_temperature: float = 0.0
    ai_max_tokens: int = 900

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def frontend_origin_list(self):
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
