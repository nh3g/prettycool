"""Integration with the psbdmp dataset."""
from __future__ import annotations

from typing import Any, Dict, List

from app.modules.base import ModuleMetadata, ModuleResult, PassiveModule


class PasteDumpModule(PassiveModule):
    """Search the psbdmp index for pastes mentioning the target."""

    metadata = ModuleMetadata(
        name="psbdmp",
        display_name="PSBDMP",
        description="Identify pastebin entries that reference the target domain.",
        category="Intelligence",
        requires_api_keys=(),
        documentation_url="https://psbdmp.ws/"
    )

    SEARCH_ENDPOINT = "https://psbdmp.ws/api/search/{target}"

    def execute(self, target: str, **options: Any) -> ModuleResult:
        payload = self.request_json("GET", self.SEARCH_ENDPOINT.format(target=target))
        data = payload.get("data", []) if isinstance(payload, dict) else []

        records: List[Dict[str, Any]] = []
        for item in data:
            paste_id = item.get("id")
            if not paste_id:
                continue
            records.append(
                {
                    "URL": f"https://pastebin.com/{paste_id}",
                    "Date": item.get("date") or item.get("time") or "Unknown",
                    "Size": item.get("size"),
                }
            )

        summary = f"Found {len(records)} paste entries mentioning {target}." if records else "No pastebin references located."
        return ModuleResult(
            metadata=self.metadata,
            success=True,
            summary=summary,
            records=records,
            raw=payload,
        )


def run(target: str, settings) -> ModuleResult:  # pragma: no cover - helper
    return PasteDumpModule(settings).execute(target)
