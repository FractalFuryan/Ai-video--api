from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    ENV: str = Field(default="dev")
    API_KEYS_ENABLED: bool = Field(default=True)

    # DB
    DATABASE_URL: str = Field(default="postgresql://harmony:harmony@db:5432/harmony4")

    # Storage
    STORAGE_BACKEND: str = Field(default="local")  # "local" | "s3"
    STORAGE_LOCAL_DIR: str = Field(default="/data/h4mk")

    # S3
    S3_BUCKET: str = Field(default="harmony4-media")
    S3_REGION: str = Field(default="us-east-1")
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_ENDPOINT_URL: str | None = None  # MinIO / R2 / custom endpoints

    # CORS
    CORS_ALLOW_ORIGINS: str = Field(default="*")  # comma-separated


settings = Settings()
