from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    app_name: str = "ISL Recognition System"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = "change-this"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"
    database_url: str = "sqlite+aiosqlite:///./isl_dev.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    models_dir: str = "../ml/models"
    static_model_path: str = "../ml/models/static_classifier"
    dynamic_model_path: str = "../ml/models/dynamic_classifier"
    sentence_model_path: str = "../ml/models/sentence_model"
    mediapipe_min_detection_confidence: float = 0.5
    mediapipe_min_tracking_confidence: float = 0.5
    rate_limit_per_minute: int = 60
    max_upload_size_mb: int = 200
    upload_dir: str = "./uploads"

    class Config:
        env_file = ".env"
        extra = "ignore"

    def get_allowed_origins(self) -> list:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
