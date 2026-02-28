"""
設定管理

環境変数から設定を読み込み、アプリケーション全体で使用する。
"""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""

    # Mistral API
    mistral_api_key: str

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"

    # Database
    database_url: str

    # Game Settings
    tick_ms: int = 200
    initial_cost: float = 10.0
    max_cost: float = 20.0
    cost_recovery_per_tick: float = 0.6
    initial_base_hp: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()
