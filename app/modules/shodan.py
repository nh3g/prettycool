"""Shodan data source integration."""
from __future__ import annotations

from typing import Any, Dict, List

from app.modules.base import ModuleMetadata, ModuleResult, PassiveModule


class ShodanModule(PassiveModule):
    """Enumerate DNS data and exposed services via the Shodan API."""

    metadata = ModuleMetadata(
        name="shodan",
        display_name="Shodan",
        description="Gather DNS information and exposed services from the Shodan search engine.",
        category="Discovery",
        requires_api_keys=("shodan",),
        documentation_url="https://developer.shodan.io/api"
    )

    DOMAIN_ENDPOINT = "https://api.shodan.io/dns/domain/{domain}"
    HOST_SEARCH_ENDPOINT = "https://api.shodan.io/shodan/host/search"

    def execute(self, target: str, **options: Any) -> ModuleResult:
        keys = self._ensure_keys()
        key = keys["shodan"]

        domain_payload = self.request_json("GET", self.DOMAIN_ENDPOINT.format(domain=target), params={"key": key})
        host_payload = self.request_json(
            "GET",
            self.HOST_SEARCH_ENDPOINT,
            params={"key": key, "query": options.get("query", f"hostname:{target}")},
        )

        subdomains = domain_payload.get("subdomains", []) if isinstance(domain_payload, dict) else []
        records = []
        if isinstance(domain_payload, dict):
            for record_type, entries in domain_payload.get("data", {}).items():
                if isinstance(entries, list):
                    records.append({"Type": record_type.upper(), "Values": entries})

        matches = host_payload.get("matches", []) if isinstance(host_payload, dict) else []
        services: List[Dict[str, Any]] = []
        for match in matches:
            services.append(
                {
                    "ip_str": match.get("ip_str"),
                    "port": match.get("port"),
                    "transport": match.get("transport"),
                    "org": match.get("org"),
                    "hostnames": match.get("hostnames"),
                    "product": match.get("product"),
                    "timestamp": match.get("timestamp"),
                }
            )
        if services:
            records.append({"Type": "Service", "Values": services})

        if subdomains or services:
            summary = f"Enumerated {len(subdomains)} subdomains and {len(services)} exposed services from Shodan."
        else:
            summary = "No Shodan data available for the target."
        return ModuleResult(
            metadata=self.metadata,
            success=True,
            summary=summary,
            records=records,
            raw={"domain": domain_payload, "services": host_payload},
        )


def run(target: str, settings) -> ModuleResult:  # pragma: no cover - helper
    return ShodanModule(settings).execute(target)
