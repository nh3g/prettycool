"""VirusTotal integration."""
from __future__ import annotations

from typing import Any, Dict, List

from app.modules.base import ModuleMetadata, ModuleResult, PassiveModule


class VirusTotalModule(PassiveModule):
    """Retrieve domain intelligence from VirusTotal."""

    metadata = ModuleMetadata(
        name="virustotal",
        display_name="VirusTotal",
        description="Fetch DNS information, related domains and recent analyses from VirusTotal.",
        category="Discovery",
        requires_api_keys=("virustotal",),
        documentation_url="https://developers.virustotal.com/reference/domains"
    )

    DOMAIN_ENDPOINT = "https://www.virustotal.com/api/v3/domains/{domain}"
    SUBDOMAIN_ENDPOINT = "https://www.virustotal.com/api/v3/domains/{domain}/subdomains"

    def execute(self, target: str, **options: Any) -> ModuleResult:
        keys = self._ensure_keys()
        headers = {"x-apikey": keys["virustotal"], "Accept": "application/json"}

        domain_payload = self.request_json("GET", self.DOMAIN_ENDPOINT.format(domain=target), headers=headers)
        subdomains_payload = self.request_json(
            "GET",
            self.SUBDOMAIN_ENDPOINT.format(domain=target),
            headers=headers,
            params={"limit": options.get("limit", 40)},
        )

        data = domain_payload.get("data", {}) if isinstance(domain_payload, dict) else {}
        attributes = data.get("attributes", {}) if isinstance(data, dict) else {}

        dns_records = attributes.get("last_dns_records", []) if isinstance(attributes, dict) else []
        categories = attributes.get("categories", {}) if isinstance(attributes, dict) else {}
        reputation = attributes.get("reputation")

        records: List[Dict[str, Any]] = []
        if isinstance(dns_records, list):
            for record in dns_records:
                if isinstance(record, dict):
                    records.append(
                        {
                            "Type": record.get("type"),
                            "Value": record.get("value"),
                            "Ttl": record.get("ttl"),
                        }
                    )

        related_data = subdomains_payload.get("data", []) if isinstance(subdomains_payload, dict) else []
        related_subdomains = [item.get("id") for item in related_data if isinstance(item, dict) and item.get("id")]
        if related_subdomains:
            records.append({"Type": "Subdomain", "Value": related_subdomains})

        summary_parts = []
        if reputation is not None:
            summary_parts.append(f"Reputation score: {reputation}")
        if categories:
            summary_parts.append("Categories: " + ", ".join(categories.values()))
        if related_subdomains:
            summary_parts.append(f"Related subdomains: {len(related_subdomains)}")
        summary = "; ".join(summary_parts) if summary_parts else "No additional intelligence provided by VirusTotal."

        return ModuleResult(
            metadata=self.metadata,
            success=True,
            summary=summary,
            records=records,
            raw={"domain": domain_payload, "subdomains": subdomains_payload},
        )


def run(target: str, settings) -> ModuleResult:  # pragma: no cover - helper
    return VirusTotalModule(settings).execute(target)
