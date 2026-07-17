from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ContextGuard API"
    app_env: str = "development"
    auth_secret: str = "contextguard-development-secret-change-me"
    auth_token_hours: int = 12
    database_url: str = "sqlite:///./contextguard.db"
    frontend_origins: str = "http://localhost:5173"
    ai_provider: str = "auto"
    mimo_api_key: str = ""
    mimo_base_url: str = "https://api.xiaomimimo.com/v1"
    mimo_model: str = "mimo-v2.5"
    mimo_secondary_model: str = "mimo-v2.5-pro"
    ai_dual_review_enabled: bool = False
    mimo_timeout_seconds: float = 30.0
    mimo_max_tokens: int = 1800
    mimo_temperature: float = 0.1
    mimo_json_mode: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def frontend_origin_list(self):
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
