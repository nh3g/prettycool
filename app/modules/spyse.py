"""Spyse intelligence module."""
from __future__ import annotations

from typing import Any, Dict, List

from app.modules.base import ModuleMetadata, ModuleResult, PassiveModule


class SpyseModule(PassiveModule):
    """Enumerate subdomains and related infrastructure via Spyse."""

    metadata = ModuleMetadata(
        name="spyse",
        display_name="Spyse",
        description="Use Spyse to enrich the target with subdomains and related domains.",
        category="Discovery",
        requires_api_keys=("spyse",),
        documentation_url="https://spyse.com/apidocs"
    )

    SUBDOMAIN_ENDPOINT = "https://api.spyse.com/v4/data/domain/subdomain"
    RELATED_ENDPOINT = "https://api.spyse.com/v4/data/domain/related"

    def execute(self, target: str, **options: Any) -> ModuleResult:
        keys = self._ensure_keys()
        headers = {"Authorization": f"Bearer {keys['spyse']}", "Accept": "application/json"}

        params = {"domain": target, "limit": options.get("limit", 100)}
        payload = self.request_json("GET", self.SUBDOMAIN_ENDPOINT, headers=headers, params=params)
        related_payload = self.request_json("GET", self.RELATED_ENDPOINT, headers=headers, params={"domain": target})

        items = payload.get("data", {}).get("items", []) if isinstance(payload, dict) else []
        related_items = related_payload.get("data", {}).get("items", []) if isinstance(related_payload, dict) else []

        subdomains = [item.get("name") for item in items if item.get("name")]
        related_domains = [item.get("name") for item in related_items if item.get("name")]

        records: List[Dict[str, Any]] = []
        if subdomains:
            records.append({"Type": "Subdomain", "Values": sorted(subdomains)})
        if related_domains:
            records.append({"Type": "Related Domain", "Values": sorted(set(related_domains))})

        summary_parts = []
        if subdomains:
            summary_parts.append(f"Subdomains: {len(subdomains)}")
        if related_domains:
            summary_parts.append(f"Related domains: {len(related_domains)}")
        summary = ", ".join(summary_parts) if summary_parts else "No Spyse intelligence available for this target."

        return ModuleResult(
            metadata=self.metadata,
            success=True,
            summary=summary,
            records=records,
            raw={"subdomains": payload, "related": related_payload},
        )


def run(target: str, settings) -> ModuleResult:  # pragma: no cover - helper
    return SpyseModule(settings).execute(target)
