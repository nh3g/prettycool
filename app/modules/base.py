"""Base classes used by PrettyCool modules.

The project keeps every data source and active scanner encapsulated in a
module object.  Each module knows how to execute its workflow and returns
structured data so the orchestrator can build reports and the front-end
can render the results.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

import requests

from app.config import Settings


@dataclass(slots=True)
class ModuleMetadata:
    """Describes a module for documentation and UI purposes."""

    name: str
    display_name: str
    description: str
    category: str
    requires_api_keys: Iterable[str] = field(default_factory=list)
    documentation_url: Optional[str] = None


@dataclass
class ModuleResult:
    """Structured response returned by every module execution."""

    metadata: ModuleMetadata
    success: bool
    summary: str
    records: List[Dict[str, Any]] = field(default_factory=list)
    raw: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)


class ModuleExecutionError(RuntimeError):
    """Raised when a module cannot finish its execution."""


class BaseModule:
    """Base implementation shared by all modules.

    Modules have access to the application :class:`Settings` and offer a
    ``request_json`` helper that keeps HTTP behaviour consistent across the
    codebase.  Concrete modules only need to implement the ``execute``
    method and populate the ``metadata`` attribute.
    """

    metadata: ModuleMetadata

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    # ------------------------------------------------------------------
    def execute(self, target: str, **options: Any) -> ModuleResult:  # pragma: no cover - abstract method
        """Execute the module logic.

        Subclasses must implement this method and return a
        :class:`ModuleResult` instance describing the outcome.
        """

        raise NotImplementedError

    # ------------------------------------------------------------------
    def _ensure_keys(self) -> Dict[str, Optional[str]]:
        """Validate the presence of required API keys."""

        keys = self.settings.api_keys.model_dump()
        missing = [key for key in self.metadata.requires_api_keys if not keys.get(key)]
        if missing:
            raise ModuleExecutionError(
                f"The following API keys are missing: {', '.join(sorted(missing))}."
            )
        return keys

    # ------------------------------------------------------------------
    def request_json(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        auth: Any = None,
    ) -> Dict[str, Any]:
        """Execute an HTTP request and return the decoded JSON payload."""

        try:
            response = requests.request(
                method,
                url,
                params=params,
                headers=headers,
                json=json_data,
                auth=auth,
                timeout=self.settings.request_timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            raise ModuleExecutionError(
                f"HTTP error calling {url}: {exc.response.status_code} {exc.response.text}"
            ) from exc
        except requests.RequestException as exc:  # pragma: no cover - defensive code
            raise ModuleExecutionError(f"Failed to reach {url}: {exc}") from exc


class PassiveModule(BaseModule):
    """Marker class for passive reconnaissance modules."""


class ActiveModule(BaseModule):
    """Marker class for active scanning modules."""
