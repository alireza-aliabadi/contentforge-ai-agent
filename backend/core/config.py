"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="ContentForge AI Agent", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    database_url: str = Field(
        default="postgresql+psycopg://contentforge:contentforge@localhost:5432/contentforge",
        alias="DATABASE_URL",
    )

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/1", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        alias="CELERY_RESULT_BACKEND",
    )

    s3_endpoint: str = Field(default="http://localhost:9000", alias="S3_ENDPOINT")
    s3_access_key: str = Field(default="minioadmin", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(default="minioadmin", alias="S3_SECRET_KEY")
    s3_bucket: str = Field(default="contentforge-assets", alias="S3_BUCKET")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    use_local_storage: bool = Field(default=True, alias="USE_LOCAL_STORAGE")
    local_storage_path: str = Field(default="./data/uploads", alias="LOCAL_STORAGE_PATH")

    llm_api_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_API_BASE_URL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    vision_api_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="VISION_API_BASE_URL",
    )
    vision_api_key: str = Field(default="", alias="VISION_API_KEY")
    vision_model: str = Field(default="gpt-4o-mini", alias="VISION_MODEL")
    embedding_api_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="EMBEDDING_API_BASE_URL",
    )
    embedding_api_key: str = Field(default="", alias="EMBEDDING_API_KEY")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    image_gen_api_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="IMAGE_GEN_API_BASE_URL",
    )
    image_gen_api_key: str = Field(default="", alias="IMAGE_GEN_API_KEY")
    image_gen_model: str = Field(default="dall-e-3", alias="IMAGE_GEN_MODEL")
    use_mock_ai: bool = Field(default=True, alias="USE_MOCK_AI")

    originality_threshold: float = Field(default=0.90, alias="ORIGINALITY_THRESHOLD")
    relevance_threshold: float = Field(default=0.90, alias="RELEVANCE_THRESHOLD")
    max_regeneration_loops: int = Field(default=3, alias="MAX_REGENERATION_LOOPS")

    otel_enabled: bool = Field(default=False, alias="OTEL_ENABLED")
    otel_service_name: str = Field(default="contentforge-api", alias="OTEL_SERVICE_NAME")
    otel_exporter_otlp_endpoint: str = Field(
        default="http://localhost:4317",
        alias="OTEL_EXPORTER_OTLP_ENDPOINT",
    )

    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    default_admin_email: str = Field(
        default="admin@contentforge.local",
        alias="DEFAULT_ADMIN_EMAIL",
    )
    default_admin_password: str = Field(default="changeme", alias="DEFAULT_ADMIN_PASSWORD")

    rate_limit: str = Field(default="100/minute", alias="RATE_LIMIT")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
