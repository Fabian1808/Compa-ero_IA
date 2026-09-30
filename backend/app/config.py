import os
import platform
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_data_dir() -> str:
    """
    Root folder for everything the app stores on the user's computer.

    Windows uses %LOCALAPPDATA%\\AIWorkmate; other platforms use the XDG data
    directory. The installer, the database, logs and the vector store all derive
    from this single value so they can never drift apart.
    """
    if platform.system() == "Windows":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return str(Path(base) / "AIWorkmate")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "AI WORKMATE"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # Storage
    # Everything the app stores lives under this folder. The defaults below are
    # derived from it unless explicitly overridden, which keeps the database,
    # the vector store and the logs in one predictable place.
    data_dir: str = Field(default_factory=default_data_dir)
    database_url: str = ""
    db_echo: bool = False
    log_file: str = ""
    qdrant_path: str = ""

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
    # Expected SHA-256 of the Ollama Windows installer.
    # Auto-install stays disabled until a real digest is pinned here, so the app
    # can never run an unverified binary.
    ollama_installer_sha256: str = ""

    # Qdrant (local embedded)

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
    log_rotation: str = "10 MB"
    log_retention: str = "7 days"

    # Tauri
    tauri_backend_port: int = 8000

    @model_validator(mode="after")
    def _derive_storage_paths(self) -> "Settings":
        root = Path(self.data_dir)
        if not self.database_url:
            db_file = (root / "database" / "ai-workmate.db").as_posix()
            self.database_url = f"sqlite+aiosqlite:///{db_file}"
        if not self.qdrant_path:
            self.qdrant_path = str(root / "ai" / "embeddings")
        if not self.log_file:
            self.log_file = str(root / "logs" / "ai-workmate.log")
        return self

    @property
    def ms_graph_authority(self) -> str:
        return f"https://login.microsoftonline.com/{self.ms_graph_tenant_id}"

    @property
    def ms_graph_scopes_list(self) -> list[str]:
        return [s.strip() for s in self.ms_graph_scopes.split() if s.strip()]


settings = Settings()
