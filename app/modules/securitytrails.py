"""SecurityTrails integration."""
from __future__ import annotations

from typing import Any, Dict, List

from app.modules.base import ModuleMetadata, ModuleResult, PassiveModule


class SecurityTrailsModule(PassiveModule):
    """Pull DNS intelligence from SecurityTrails."""

    metadata = ModuleMetadata(
        name="securitytrails",
        display_name="SecurityTrails",
        description="Retrieve DNS records, subdomains and infrastructure data from SecurityTrails.",
        category="Discovery",
        requires_api_keys=("securitytrails",),
        documentation_url="https://docs.securitytrails.com/reference/overview"
    )

    def execute(self, target: str, **options: Any) -> ModuleResult:
        keys = self._ensure_keys()
        headers = {"Accept": "application/json", "APIKEY": keys["securitytrails"]}

        domain_details = self.request_json("GET", f"https://api.securitytrails.com/v1/domain/{target}", headers=headers)
        subdomains_payload = self.request_json(
            "GET",
            f"https://api.securitytrails.com/v1/domain/{target}/subdomains",
            headers=headers,
            params={"children_only": "false"},
        )

        apex = domain_details.get("current_dns", {}) if isinstance(domain_details, dict) else {}

        summary_parts: List[str] = []
        if isinstance(apex, dict):
            if "a" in apex:
                summary_parts.append(f"A records: {len(apex['a'])}")
            if "mx" in apex:
                summary_parts.append(f"MX servers: {len(apex['mx'])}")
            if "ns" in apex:
                summary_parts.append(f"NS records: {len(apex['ns'])}")
        summary = ", ".join(summary_parts) if summary_parts else "No active DNS records returned."

        subdomains_payload_data = subdomains_payload.get("subdomains", []) if isinstance(subdomains_payload, dict) else []
        subdomains = [f"{item}.{target}" for item in subdomains_payload_data if isinstance(item, str)]

        records: List[Dict[str, Any]] = []
        if isinstance(apex, dict):
            for record_type, entries in apex.items():
                values: List[str] = []
                if isinstance(entries, list):
                    for entry in entries:
                        if isinstance(entry, dict):
                            values.append(entry.get("ip") or entry.get("value") or str(entry))
                        else:
                            values.append(str(entry))
                if values:
                    records.append({"Type": record_type.upper(), "Values": values})
        if subdomains:
            records.append({"Type": "Subdomain", "Values": sorted(subdomains)})

        return ModuleResult(
            metadata=self.metadata,
            success=True,
            summary=summary,
            records=records,
            raw={"domain": domain_details, "subdomains": subdomains_payload},
        )


def run(target: str, settings) -> ModuleResult:  # pragma: no cover - helper
    return SecurityTrailsModule(settings).execute(target)
