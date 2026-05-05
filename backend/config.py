from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # App
    secret_key: str = "change-me"
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost", "http://localhost:5173"])

    # DB
    postgres_url: str = "postgresql://seolab:seolab@db:5432/seolab"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # DataForSEO
    dataforseo_login: str = ""
    dataforseo_password: str = ""

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"

    # Google
    google_client_id: str = ""
    google_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost/api/gsc/oauth/callback"
    google_pagespeed_api_key: str = ""

    # Open PageRank
    open_pagerank_api_key: str = ""

    # Crawler
    crawler_user_agent: str = "SEOLabBot/1.0 (+https://seolab.local)"
    crawler_max_pages: int = 500
    crawler_rate_limit_rps: float = 1.0

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def async_db_url(self) -> str:
        url = self.postgres_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_db_url(self) -> str:
        url = self.postgres_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
