"""
Shared test fixtures.

Every test runs against an isolated data folder so a test run can never touch
the real database, logs or caches stored under the user's AppData directory.
"""

import importlib
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    """
    Point every storage path at a throwaway folder for the duration of a test.

    Modules that capture settings at import time are reloaded afterwards so they
    pick up the isolated paths instead of the real ones.
    """
    with tempfile.TemporaryDirectory(prefix="aiworkmate-test-") as tmp:
        monkeypatch.setenv("LOCALAPPDATA", tmp)
        monkeypatch.setenv("DATA_DIR", str(Path(tmp) / "AIWorkmate"))
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.setenv("QDRANT_PATH", "")
        monkeypatch.setenv("LOG_FILE", "")

        from app import config

        reloaded = config.Settings()
        monkeypatch.setattr(config, "settings", reloaded)

        services = importlib.import_module("app.services.installer_service")
        monkeypatch.setattr(services, "settings", reloaded)
        monkeypatch.setattr(
            services,
            "first_run_marker",
            services.FirstRunMarker(Path(reloaded.data_dir)),
        )

        yield Path(reloaded.data_dir)
