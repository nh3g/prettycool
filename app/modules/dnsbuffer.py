"""DnsBuffer module using the BufferOver API."""
from __future__ import annotations

from typing import Any, Dict, List

from app.modules.base import ModuleMetadata, ModuleResult, PassiveModule


class DNSBufferModule(PassiveModule):
    """Fetch passive DNS records from BufferOver."""

    metadata = ModuleMetadata(
        name="dnsbuffer",
        display_name="BufferOver DNS",
        description="Collect hostnames and IPv4 pairs from passive DNS caches.",
        category="Discovery",
        requires_api_keys=(),
        documentation_url="https://dns.bufferover.run/"
    )

    def execute(self, target: str, **options: Any) -> ModuleResult:
        payload = self.request_json("GET", "https://dns.bufferover.run/dns", params={"q": target})

        fdns = payload.get("FDNS_A", [])
        host_records: List[Dict[str, Any]] = []
        for entry in fdns or []:
            try:
                ip, hostname = entry.split(",", 1)
            except ValueError:
                continue
            if hostname.endswith(target):
                host_records.append({"Hostname": hostname, "IPv4": ip})

        summary = f"Identified {len(host_records)} hostnames through passive DNS." if host_records else "No passive DNS data returned."
        return ModuleResult(
            metadata=self.metadata,
            success=True,
            summary=summary,
            records=host_records,
            raw=payload,
        )


def run(target: str, settings) -> ModuleResult:  # pragma: no cover - helper
    return DNSBufferModule(settings).execute(target)
