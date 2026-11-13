"""集中配置：全部来自环境变量，默认值与 .env.example 保持一致。"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "sampleaqp"
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "sampleaqp"
    db_user: str = "sampleaqp"
    db_password: str = "sampleaqp_pw_2026"

    jwt_secret: str = "sampleaqp-jwt-secret-change-me-2026"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480

    redis_url: str = "redis://localhost:6379/0"
    seed_demo: bool = True
    rate_limit_per_minute: int = 300
    rate_limit_write_per_minute: int = 60
    app_timezone_offset_minutes: int = 480

    # 抽样域常量（可在 .env 覆盖，便于不同项目复用）
    min_stratum_sample: int = 30
    min_total_sample: int = 60
    export_prefix: str = "sampleaqp"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
