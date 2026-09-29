from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "AI Workmate"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/ai-workmate.db"
    db_echo: bool = False

    # Microsoft Graph (Work/School only)
    ms_graph_client_id: str = ""
    ms_graph_client_secret: str = ""
    ms_graph_tenant_id: str = "organizations"
    ms_graph_redirect_uri: str = "http://localhost:8000/api/v1/auth/callback"
    ms_graph_scopes: str = "Mail.Read Mail.ReadWrite Calendars.Read Contacts.Read User.Read"

    # Encryption
    encryption_master_key: str = ""

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "phi3:3.8b"
    ollama_embed_model: str = "nomic-embed-text"

    # Qdrant (local embedded)
    qdrant_path: str = "./data/qdrant"

    # Sync
    sync_interval_minutes: int = 5
    sync_batch_size: int = 100
    delta_sync_enabled: bool = True

    # AI
    ai_temperature: float = 0.1
    ai_max_tokens: int = 2048
    ai_confidence_auto_create: int = 95
    ai_confidence_suggest: int = 80

    # Notifications
    notification_check_interval_minutes: int = 1
    daily_briefing_hour: int = 8
    end_of_day_hour: int = 18

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/ai-workmate.log"
    log_rotation: str = "10 MB"
    log_retention: str = "7 days"

    # Tauri
    tauri_backend_port: int = 8000

    @property
    def ms_graph_authority(self) -> str:
        return f"https://login.microsoftonline.com/{self.ms_graph_tenant_id}"

    @property
    def ms_graph_scopes_list(self) -> list[str]:
        return [s.strip() for s in self.ms_graph_scopes.split() if s.strip()]


settings = Settings()