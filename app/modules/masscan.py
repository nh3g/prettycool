from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any, Dict, List

from app.modules.base import ActiveModule, ModuleExecutionError, ModuleMetadata, ModuleResult


class MasscanModule(ActiveModule):
    """Wrapper around the masscan binary."""

    metadata = ModuleMetadata(
        name="masscan",
        display_name="Masscan",
        description="Execute masscan locally to discover open TCP ports.",
        category="Active",
        requires_api_keys=(),
        documentation_url="https://github.com/robertdavidgraham/masscan"
    )

    def execute(self, target: str, **options: Any) -> ModuleResult:
        binary = shutil.which("masscan")
        if not binary:
            raise ModuleExecutionError("masscan binary not found. Install masscan or adjust PATH to enable active scanning.")

        ports = options.get("ports", "1-65535")
        rate = str(options.get("rate", 1000))
        command = [binary, target, f"-p{ports}", f"--rate={rate}", "--wait", "0", "-oJ", "-"]

        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:  # pragma: no cover - defensive code
            raise ModuleExecutionError(f"Failed to execute masscan: {exc}") from exc

        if process.returncode not in (0, 1):
            raise ModuleExecutionError(
                f"masscan exited with status {process.returncode}: {process.stderr.strip()}"
            )

        results: List[Dict[str, Any]] = []
        for raw_line in process.stdout.splitlines():
            line = raw_line.strip().rstrip(",")
            if not line or line in {"[", "]"}:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            ports_data = data.get("ports", [])
            for port in ports_data:
                results.append(
                    {
                        "ip": data.get("ip"),
                        "port": port.get("port"),
                        "protocol": port.get("proto"),
                        "status": port.get("status"),
                    }
                )

        summary = f"masscan identified {len(results)} open ports." if results else "masscan did not report any open ports."
        return ModuleResult(
            metadata=self.metadata,
            success=True,
            summary=summary,
            records=results,
            raw={"stdout": process.stdout, "stderr": process.stderr},
        )


def run(target: str, settings) -> ModuleResult:  # pragma: no cover - helper
    return MasscanModule(settings).execute(target)
