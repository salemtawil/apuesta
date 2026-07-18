from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BetAlpha Manager"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./betalpha_dev.db"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    demo_user_id: str = "00000000-0000-4000-8000-000000000001"
    max_upload_mb: int = 8
    default_fractional_kelly: float = 0.25
    default_max_stake_pct: float = 0.015
    default_daily_exposure_pct: float = 0.05
    the_odds_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("THE_ODDS_API_KEY", "BETALPHA_THE_ODDS_API_KEY"),
    )

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_prefix="BETALPHA_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
