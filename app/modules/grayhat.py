"""GrayHat Warfare S3 bucket discovery module."""
from __future__ import annotations

from typing import Any, Dict, List, Set

from app.modules.base import ModuleMetadata, ModuleResult, PassiveModule


class GrayHatWarfareModule(PassiveModule):
    """Search publicly indexed S3 buckets for keywords related to the target."""

    metadata = ModuleMetadata(
        name="grayhat",
        display_name="GrayHat Warfare",
        description="Discover public cloud storage buckets that mention the target organization.",
        category="Intelligence",
        requires_api_keys=("grayhat",),
        documentation_url="https://buckets.grayhatwarfare.com/docs/api/v1"
    )

    BASE_ENDPOINT = "https://buckets.grayhatwarfare.com/api/v1"

    def execute(self, target: str, **options: Any) -> ModuleResult:
        keys = self._ensure_keys()
        token = keys["grayhat"]
        keywords = self._build_keyword_list(target)
        limit = options.get("max_keywords", 20)

        discovered: Dict[str, Dict[str, Any]] = {}
        for keyword in keywords[:limit]:
            params = {"access_token": token, "keywords": keyword}
            payload = self.request_json("GET", f"{self.BASE_ENDPOINT}/buckets/0/100", params=params)
            for bucket in payload.get("buckets", []) if isinstance(payload, dict) else []:
                name = bucket.get("bucket")
                if not name:
                    continue
                discovered[name] = {
                    "Keyword": keyword,
                    "Bucket": name,
                    "Id": bucket.get("id"),
                    "Region": bucket.get("region"),
                    "Files": bucket.get("files"),
                }

        records = list(discovered.values())
        summary = (
            f"Identified {len(records)} buckets that reference the target across {min(limit, len(keywords))} keywords."
            if records
            else "No buckets matched the generated keyword list."
        )

        return ModuleResult(
            metadata=self.metadata,
            success=True,
            summary=summary,
            records=records,
            raw={"buckets": records},
        )

    # ------------------------------------------------------------------
    def _build_keyword_list(self, domain: str) -> List[str]:
        parts = [segment for segment in domain.replace("-", ".").split(".") if segment and len(segment) > 2]
        keywords: Set[str] = set()
        if domain:
            keywords.add(domain)
        for part in parts:
            keywords.add(part)
        if len(parts) > 1:
            keywords.add("-".join(parts))
            keywords.add("".join(parts))
        return sorted(keywords)


def run(target: str, settings) -> ModuleResult:  # pragma: no cover - helper
    return GrayHatWarfareModule(settings).execute(target)
