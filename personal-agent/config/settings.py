"""Application settings and configuration."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Gemini Configuration
    gemini_api_key: str = Field(..., description="Google Gemini API Key")
    default_model: str = Field(default="gemini-pro", description="Default model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, gt=0)

    # Web UI Configuration
    web_host: str = Field(default="0.0.0.0")
    web_port: int = Field(default=8000, gt=0, lt=65536)

    # Redis Configuration
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379, gt=0, lt=65536)
    redis_db: int = Field(default=0, ge=0)

    # Database Configuration
    database_url: str = Field(default="sqlite+aiosqlite:///./personal_agent.db")

    # Agent Configuration
    agent_name: str = Field(default="Personal Agent")
    check_interval_minutes: int = Field(default=30, gt=0)

    # Logging
    log_level: str = Field(default="INFO")
    log_file: Optional[str] = Field(default=None)

    def get_llm_config(self):
        """Get LLM configuration from settings."""
        from src.llm import LLMConfig, ModelProvider

        return LLMConfig(
            provider=ModelProvider.GEMINI,
            model_name=self.default_model,
            api_key=self.gemini_api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )


# Global settings instance
settings = Settings()
