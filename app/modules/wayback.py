"""Wayback Machine passive web enumeration."""
from __future__ import annotations

from typing import Any, List

from app.modules.base import ModuleMetadata, ModuleResult, PassiveModule


class WaybackModule(PassiveModule):
    """Enumerate historical URLs using the Internet Archive."""

    metadata = ModuleMetadata(
        name="wayback",
        display_name="Wayback Machine",
        description="Discover historical URLs captured by the Internet Archive.",
        category="Intelligence",
        requires_api_keys=(),
        documentation_url="https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server"
    )

    ENDPOINT = "https://web.archive.org/cdx/search/cdx"

    def execute(self, target: str, **options: Any) -> ModuleResult:
        params = {
            "url": f"*.{target}/*",
            "output": "json",
            "collapse": "urlkey",
            "filter": "statuscode:200",
            "limit": options.get("limit", 200),
        }
        payload = self.request_json("GET", self.ENDPOINT, params=params)

        urls: List[str] = []
        if isinstance(payload, list) and payload:
            for row in payload[1:]:  # Skip header row
                if len(row) >= 3:
                    urls.append(row[2])

        sample_size = min(options.get("sample", 10), len(urls))
        records = [{"URL": url} for url in urls[:sample_size]]
        summary = f"Identified {len(urls)} archived URLs; showing {sample_size} examples."
        if not urls:
            summary = "No archived content found for the target."

        return ModuleResult(
            metadata=self.metadata,
            success=True,
            summary=summary,
            records=records,
            raw={"urls": urls},
        )


def run(target: str, settings) -> ModuleResult:  # pragma: no cover - helper
    return WaybackModule(settings).execute(target)
