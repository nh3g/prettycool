"""WhoisFreaks module implementation."""
from __future__ import annotations

from typing import Any, Dict

from app.modules.base import ModuleMetadata, ModuleResult, PassiveModule


class WhoisFreaksModule(PassiveModule):
    """Retrieve WHOIS information using the WhoisFreaks API."""

    metadata = ModuleMetadata(
        name="whoisfreaks",
        display_name="WhoisFreaks",
        description="Collect detailed WHOIS records, including historical snapshots, for the target domain.",
        category="Discovery",
        requires_api_keys=("whoisfreaks",),
        documentation_url="https://api.whoisfreaks.com/"
    )

    def execute(self, target: str, **options: Any) -> ModuleResult:
        keys = self._ensure_keys()
        params = {
            "apiKey": keys["whoisfreaks"],
            "domainName": target,
            "whois": options.get("mode", "current"),
        }
        payload = self.request_json("GET", "https://api.whoisfreaks.com/v1.0/whois", params=params)

        summary_fields = {
            "Domain": payload.get("domain_name"),
            "Registrar": payload.get("registrar"),
            "Created At": payload.get("created_date"),
            "Updated At": payload.get("updated_date"),
            "Expires At": payload.get("expiry_date"),
        }
        summary_text = ", ".join(f"{label}: {value}" for label, value in summary_fields.items() if value)
        if not summary_text:
            summary_text = "No WHOIS summary fields were returned."

        contacts: Dict[str, Dict[str, Any]] = payload.get("contacts", {}) if isinstance(payload, dict) else {}
        records = []
        for section, data in contacts.items():
            if isinstance(data, dict):
                formatted = {key.replace("_", " ").title(): value for key, value in data.items() if value}
                if formatted:
                    records.append({"section": section.title(), "data": formatted})

        return ModuleResult(
            metadata=self.metadata,
            success=True,
            summary=summary_text,
            records=records,
            raw=payload,
        )


def run(target: str, settings) -> ModuleResult:  # pragma: no cover - convenience wrapper
    """Helper used by the CLI and console mode."""

    module = WhoisFreaksModule(settings)
    return module.execute(target)
