"""Markdown reporting utilities."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from app.modules import ModuleResult


class MarkdownBuilder:
    """Convert module results into a human readable Markdown document."""

    def __init__(self, target: str, mode: str, results: Iterable[ModuleResult]) -> None:
        self.target = target
        self.mode = mode
        self.results = list(results)

    # ------------------------------------------------------------------
    def build(self) -> str:
        lines: List[str] = []
        lines.append("# PrettyCool Reconnaissance Report")
        lines.append("")
        lines.append(f"- **Target:** {self.target}")
        lines.append(f"- **Mode:** {self.mode}")
        lines.append(f"- **Generated at:** {datetime.utcnow().isoformat()}Z")
        lines.append("")

        for result in self.results:
            metadata = result.metadata
            lines.append(f"## {metadata.display_name} ({metadata.category})")
            lines.append("")
            status = "Success" if result.success else "Failure"
            lines.append(f"**Status:** {status}")
            lines.append("")
            lines.append(f"**Summary:** {result.summary}")
            lines.append("")
            if result.records:
                lines.append("### Records")
                lines.extend(self._format_records(result.records))
            if result.errors:
                lines.append("### Errors")
                for error in result.errors:
                    lines.append(f"- {error}")
            lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def _format_records(self, records) -> List[str]:
        formatted: List[str] = []
        for index, record in enumerate(records, 1):
            formatted.append(f"- **Record {index}**")
            if isinstance(record, dict):
                for key, value in record.items():
                    if isinstance(value, (dict, list)):
                        pretty = json.dumps(value, indent=2, ensure_ascii=False)
                        formatted.append(f"  - **{key}:**\n\n````\n{pretty}\n````")
                    else:
                        formatted.append(f"  - **{key}:** {value}")
            else:
                formatted.append(f"  - {record}")
        formatted.append("")
        return formatted

    # ------------------------------------------------------------------
    def save(self, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.build(), encoding="utf-8")
        return destination
