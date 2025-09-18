"""CertSpotter discovery module."""
from __future__ import annotations

from typing import Any, Dict, List

from app.modules.base import ModuleExecutionError, ModuleMetadata, ModuleResult, PassiveModule


class CertSpotterModule(PassiveModule):
    """Enumerate certificates issued for the target using the CertSpotter API."""

    metadata = ModuleMetadata(
        name="certspotter",
        display_name="CertSpotter",
        description="Enumerate hostnames from TLS certificates indexed by CertSpotter.",
        category="Discovery",
        requires_api_keys=(),
        documentation_url="https://sslmate.com/certspotter/api/"
    )

    def execute(self, target: str, **options: Any) -> ModuleResult:
        keys = self.settings.api_keys.model_dump()
        headers = {"Accept": "application/json"}
        if keys.get("certspotter"):
            headers["Authorization"] = f"Bearer {keys['certspotter']}"

        params = {
            "domain": target,
            "expand": ["dns_names", "issuer"],
            "match_wildcards": "true",
        }
        payload = self.request_json("GET", "https://api.certspotter.com/v1/issuances", params=params, headers=headers)
        if not isinstance(payload, list):
            raise ModuleExecutionError("Unexpected payload returned by the CertSpotter API.")

        hostnames: List[str] = []
        issuers: Dict[str, int] = {}
        for certificate in payload:
            dns_names = certificate.get("dns_names", [])
            for name in dns_names:
                if target in name and name not in hostnames:
                    hostnames.append(name)
            issuer = certificate.get("issuer", {}).get("common_name")
            if issuer:
                issuers[issuer] = issuers.get(issuer, 0) + 1

        records = [{"Hostname": hostname} for hostname in sorted(hostnames)]
        summary = f"Identified {len(hostnames)} unique hostnames across {len(payload)} certificates."
        if issuers:
            top_issuer, count = sorted(issuers.items(), key=lambda item: item[1], reverse=True)[0]
            summary += f" Most common issuer: {top_issuer} ({count} certificates)."

        return ModuleResult(
            metadata=self.metadata,
            success=True,
            summary=summary,
            records=records,
            raw={"certificates": payload},
        )


def run(target: str, settings) -> ModuleResult:  # pragma: no cover - helper
    return CertSpotterModule(settings).execute(target)
