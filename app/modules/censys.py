"""Censys host discovery module."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.modules.base import ModuleExecutionError, ModuleMetadata, ModuleResult, PassiveModule


class CensysModule(PassiveModule):
    """Leverage the Censys v2 API to enumerate hosts and services."""

    metadata = ModuleMetadata(
        name="censys",
        display_name="Censys",
        description="Discover hosts, services and certificates indexed by Censys.",
        category="Discovery",
        requires_api_keys=("censys_id", "censys_secret"),
        documentation_url="https://search.censys.io/api"
    )

    SEARCH_ENDPOINT = "https://search.censys.io/api/v2/hosts/search"
    HOST_ENDPOINT = "https://search.censys.io/api/v2/hosts/{ip}"

    def execute(self, target: str, **options: Any) -> ModuleResult:
        keys = self._ensure_keys()
        auth: Tuple[str, str] = (keys["censys_id"], keys["censys_secret"])  # type: ignore[arg-type]

        query = options.get(
            "query",
            f"services.dns.names: \"{target}\" OR services.tls.certificates.leaf_data.subject.common_name: \"{target}\" OR services.tls.certificates.leaf_data.extensions.subject_alt_name.dns_names: \"{target}\"",
        )
        params = {"q": query, "per_page": options.get("per_page", 50), "virtual_hosts": "EXCLUDE"}
        payload = self.request_json("GET", self.SEARCH_ENDPOINT, params=params, auth=auth)

        result_section = payload.get("result", {}) if isinstance(payload, dict) else {}
        hits = result_section.get("hits", [])
        if not isinstance(hits, list):
            raise ModuleExecutionError("Unexpected payload returned by the Censys API.")

        include_details = options.get("include_details", True)
        host_records: List[Dict[str, Any]] = []
        for hit in hits:
            ip_address = hit.get("ip")
            if not ip_address:
                continue
            location = hit.get("location", {})
            services = [service.get("service_name") for service in hit.get("services", []) if service.get("service_name")]
            record: Dict[str, Any] = {
                "IPv4": ip_address,
                "Location": {
                    "country": location.get("country"),
                    "city": location.get("city"),
                    "coordinates": location.get("coordinates"),
                },
                "Observed Services": services,
                "Last Seen": hit.get("last_updated_at"),
            }

            if include_details:
                details = self.request_json("GET", self.HOST_ENDPOINT.format(ip=ip_address), auth=auth)
                record["Details"] = self._simplify_services(details.get("result", {}).get("services", []))

            host_records.append(record)

        summary = f"Identified {len(host_records)} hosts indexed by Censys." if host_records else "No hosts found in Censys."
        return ModuleResult(
            metadata=self.metadata,
            success=True,
            summary=summary,
            records=host_records,
            raw=payload,
        )

    # ------------------------------------------------------------------
    def _simplify_services(self, services: Any) -> List[Dict[str, Any]]:
        simplified: List[Dict[str, Any]] = []
        if not isinstance(services, list):
            return simplified
        for service in services:
            if not isinstance(service, dict):
                continue
            entry = {
                "port": service.get("port"),
                "service_name": service.get("service_name"),
                "transport_protocol": service.get("transport_protocol"),
            }
            http_info = service.get("http", {})
            if isinstance(http_info, dict):
                response = http_info.get("response", {})
                if isinstance(response, dict):
                    entry["http"] = {
                        "status_code": response.get("status_code"),
                        "server": (response.get("headers", {}) or {}).get("Server"),
                        "title": response.get("body", "")[:120],
                    }
            simplified.append(entry)
        return simplified


def run(target: str, settings) -> ModuleResult:  # pragma: no cover - helper
    return CensysModule(settings).execute(target)
