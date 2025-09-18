"""Configuration helpers for the PrettyCool web application.

This module centralises the loading and persistence of configuration
information required by the application.  The original CLI tool stored
credentials in Python files; in this rewrite we move the settings to a
JSON document so both the API and the front-end can update the
configuration without editing code manually.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field

# Default location for the persisted configuration file.
CONFIG_PATH = Path("config/settings.json")


class APIKeys(BaseModel):
    """Represents all API keys supported by the platform.

    Each attribute can be ``None`` when the key was not provided yet.  The
    list covers every external data source supported by the original
    PrettyCool implementation.  Additional keys can be appended without
    breaking backwards compatibility.
    """

    censys_id: Optional[str] = Field(default=None, description="Censys API ID")
    censys_secret: Optional[str] = Field(default=None, description="Censys API secret")
    shodan: Optional[str] = Field(default=None, description="Shodan API key")
    virustotal: Optional[str] = Field(default=None, description="VirusTotal API key")
    securitytrails: Optional[str] = Field(default=None, description="SecurityTrails API key")
    spyse: Optional[str] = Field(default=None, description="Spyse API token")
    grayhat: Optional[str] = Field(default=None, description="GrayHat Warfare API token")
    whoisfreaks: Optional[str] = Field(default=None, description="WhoisFreaks API key")
    certspotter: Optional[str] = Field(default=None, description="CertSpotter API key")
    pastebin: Optional[str] = Field(default=None, description="Pastebin API key")
    aws_access_key: Optional[str] = Field(default=None, description="AWS access key for S3 discovery")
    aws_secret_key: Optional[str] = Field(default=None, description="AWS secret key for S3 discovery")


class Settings(BaseModel):
    """Main configuration object persisted on disk."""

    api_keys: APIKeys = Field(default_factory=APIKeys)
    request_timeout: int = Field(default=30, description="HTTP timeout (seconds) for outbound requests")


class SettingsManager:
    """Utility class responsible for loading and persisting :class:`Settings`.

    The manager keeps the configuration cached in memory and writes any
    update to disk immediately.  This behaviour mirrors configuration
    panels in production systems and is convenient for the front-end as it
    avoids restarts when a key changes.
    """

    def __init__(self, path: Path = CONFIG_PATH) -> None:
        self.path = path
        self._settings = Settings()
        self._ensure_storage()
        self._load_from_disk()

    # ------------------------------------------------------------------
    def _ensure_storage(self) -> None:
        """Create the configuration directory and placeholder file."""

        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            # Persist a default configuration so operators know which keys
            # are expected even before opening the UI.
            self.save(self._settings)

    # ------------------------------------------------------------------
    def _load_from_disk(self) -> None:
        """Load the configuration file content into memory."""

        try:
            raw_data = json.loads(self.path.read_text(encoding="utf-8"))
            self._settings = Settings(**raw_data)
        except FileNotFoundError:
            # The file is created lazily by :meth:`_ensure_storage`.  When
            # it was removed manually we simply re-create it using the
            # default configuration.
            self.save(self._settings)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive code
            raise ValueError("Invalid JSON structure in configuration file") from exc

    # ------------------------------------------------------------------
    @property
    def settings(self) -> Settings:
        """Return a copy of the current settings instance."""

        return self._settings.copy()

    # ------------------------------------------------------------------
    def save(self, settings: Optional[Settings] = None) -> None:
        """Persist configuration to disk.

        Parameters
        ----------
        settings:
            Optional :class:`Settings` instance to persist.  When omitted
            the currently cached settings are used.
        """

        target = settings or self._settings
        self.path.write_text(target.model_dump_json(indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    def update_api_keys(self, updates: Dict[str, Optional[str]]) -> Settings:
        """Update API keys while keeping other configuration untouched."""

        current_keys = self._settings.api_keys.model_copy()
        for key, value in updates.items():
            if hasattr(current_keys, key):
                setattr(current_keys, key, value or None)
        self._settings = self._settings.model_copy(update={"api_keys": current_keys})
        self.save(self._settings)
        return self.settings

    # ------------------------------------------------------------------
    def update_timeout(self, timeout: int) -> Settings:
        """Update the default HTTP timeout used by the modules."""

        self._settings = self._settings.model_copy(update={"request_timeout": timeout})
        self.save(self._settings)
        return self.settings


# Shared singleton used across the application.  FastAPI will import this
# module only once which is sufficient for the purposes of this project.
settings_manager = SettingsManager()
