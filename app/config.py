"""Модуль конфигурации приложения"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
       Класс конфигурации приложения

       Attributes:
           database_url: Строка подключения к базе данных
           api_key: API ключ для авторизации HTTP-запросов
    """
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        extra="ignore",
    )

    database_url: str
    api_key: str


settings = Settings()
