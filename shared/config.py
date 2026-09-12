from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EDU_", extra="ignore")
    service_name: str = "auth-service"
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "educapilote"
    db_user: str = "edu_auth"
    db_password_file: Path = Path("/run/secrets/db_password")
    redis_host: str = "redis"
    redis_username: str = "default"
    redis_db: int = Field(default=0, ge=0, le=15)
    redis_password_file: Path = Path("/run/secrets/redis_password")
    db_pool_size: int = Field(default=2, ge=1, le=10)
    jwt_public_keys_file: Path = Path("/run/secrets/jwt_public_keys")
    jwt_private_key_file: Path = Path("/run/secrets/jwt_private_key")
    jwt_active_kid: str = "edu-key-1"
    jwt_issuer: str = "educapilote"
    jwt_audience: str = "educapilote-api"
    access_token_seconds: int = Field(default=300, ge=60, le=900)
    refresh_token_seconds: int = Field(default=604800, ge=600, le=604800)
    pii_keys_file: Path = Path("/run/secrets/pii_keys")
    rate_key_file: Path = Path("/run/secrets/rate_key")
    safety_model: str = "fr_core_news_sm"
    safety_retention_days: int = Field(default=7, ge=1, le=30)
    ollama_url: str = "http://ollama-host:11434"
    cloud_model: str = "gpt-oss:120b-cloud"
    embedding_model: str = "educapilote-embeddinggemma:v1"
    internal_key_file: Path = Path("/run/secrets/ai_internal_key")
    ai_daily_calls: int = Field(default=200, ge=1, le=10000)
    safety_url: str = "http://safety-service:8000"
    retrieval_url: str = "http://retrieval-service:8000"
    router_url: str = "http://ai-router-service:8000"
    automation_keys_file: Path = Path("/run/secrets/automation_keys")

    def database_url(self) -> URL:
        return URL.create("postgresql+psycopg", username=self.db_user,
            password=self.db_password_file.read_text().strip(), host=self.db_host,
            port=self.db_port, database=self.db_name)
