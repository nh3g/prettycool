from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from app.orchestrator import ModuleOrchestrator
from app.reporting import MarkdownBuilder


@dataclass
class ConsoleResponse:
    success: bool
    output: str
    markdown_path: str | None = None


class ConsoleEngine:
    """Parse textual commands and execute the appropriate module workflows."""

    def __init__(self, orchestrator: ModuleOrchestrator) -> None:
        self.orchestrator = orchestrator

    def execute(self, command: str) -> ConsoleResponse:
        command = command.strip()
        if not command:
            return ConsoleResponse(success=False, output="No command provided. Type 'help' to list available commands.")

        try:
            tokens = shlex.split(command)
        except ValueError as exc:
            return ConsoleResponse(success=False, output=f"Failed to parse command: {exc}")

        if not tokens:
            return ConsoleResponse(success=False, output="No command provided. Type 'help' to list available commands.")

        action = tokens[0].lower()
        if action == "help":
            return ConsoleResponse(success=True, output=self._help_text())
        if action == "list":
            return self._handle_list(tokens[1:])
        if action == "run":
            return self._handle_run(tokens[1:])
        return ConsoleResponse(success=False, output=f"Unknown command '{action}'. Type 'help' for usage information.")

    def _help_text(self) -> str:
        return (
            "Available commands:\n"
            "  help                               Show this message.\n"
            "  list modules                       List available modules.\n"
            "  run module <name> --target <tgt>  Execute a specific module.\n"
            "  run bundle <category> --target <tgt>  Execute all modules within a category.\n"
            "  run all --target <tgt>             Execute every module sequentially.\n"
            "Options can be provided using --key value (for example: --limit 20)."
        )

    def _handle_list(self, tokens: List[str]) -> ConsoleResponse:
        if tokens and tokens[0].lower() == "modules":
            modules = self.orchestrator.available_modules()
            lines = ["Available modules:"]
            for module in modules:
                lines.append(f"- {module.name} ({module.category}) - {module.description}")
            return ConsoleResponse(success=True, output="\n".join(lines))
        return ConsoleResponse(success=False, output="Unknown list command. Did you mean 'list modules'? ")

    def _handle_run(self, tokens: List[str]) -> ConsoleResponse:
        if not tokens:
            return ConsoleResponse(success=False, output="Missing arguments for run command.")

        target, options = self._extract_target_and_options(tokens)
        if not target:
            return ConsoleResponse(success=False, output="Target not specified. Use --target <value>.")

        mode = tokens[0].lower()
        if mode == "module":
            if len(tokens) < 2:
                return ConsoleResponse(success=False, output="Module name missing.")
            module_name = tokens[1]
            if module_name not in {metadata.name for metadata in self.orchestrator.available_modules()}:
                return ConsoleResponse(success=False, output=f"Unknown module '{module_name}'.")
            result = self.orchestrator.run_module(module_name, target, **options)
            builder = MarkdownBuilder(target, f"module-{module_name}", [result])
            report_path = builder.save(Path("reports") / self.orchestrator.timestamped_report_name(target, module_name))
            output = self._format_module_result(result)
            return ConsoleResponse(success=result.success, output=output, markdown_path=str(report_path))

        if mode == "bundle":
            if len(tokens) < 2:
                return ConsoleResponse(success=False, output="Bundle name missing.")
            bundle = tokens[1].lower()
            available = self.orchestrator.categories()
            lower_map = {key.lower(): key for key in available}
            if bundle not in lower_map:
                valid = ", ".join(sorted(available.keys()))
                return ConsoleResponse(success=False, output=f"Unknown bundle '{bundle}'. Available: {valid}")
            actual_bundle = lower_map[bundle]
            modules = [module.name for module in available[actual_bundle]]
            results = self.orchestrator.run_bundle(modules, target, **options)
            builder = MarkdownBuilder(target, f"bundle-{bundle}", results)
            report_path = builder.save(Path("reports") / self.orchestrator.timestamped_report_name(target, bundle))
            output = "\n\n".join(self._format_module_result(res) for res in results)
            success = all(res.success for res in results)
            return ConsoleResponse(success=success, output=output, markdown_path=str(report_path))

        if mode == "all":
            modules = [module.name for module in sorted(self.orchestrator.available_modules(), key=lambda m: m.name)]
            results = self.orchestrator.run_bundle(modules, target, **options)
            builder = MarkdownBuilder(target, "full-run", results)
            report_path = builder.save(Path("reports") / self.orchestrator.timestamped_report_name(target, "all"))
            output = "\n\n".join(self._format_module_result(res) for res in results)
            success = all(res.success for res in results)
            return ConsoleResponse(success=success, output=output, markdown_path=str(report_path))

        return ConsoleResponse(success=False, output=f"Unknown run mode '{mode}'.")

    def _extract_target_and_options(self, tokens: List[str]) -> Tuple[str | None, Dict[str, str]]:
        target: str | None = None
        options: Dict[str, str] = {}
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if token in {"--target", "-t"}:
                if index + 1 < len(tokens):
                    target = tokens[index + 1]
                    index += 2
                    continue
            if token.startswith("--") and index + 1 < len(tokens):
                options[token[2:]] = tokens[index + 1]
                index += 2
                continue
            index += 1
        return target, options

    def _format_module_result(self, result) -> str:
        lines = [f"[{result.metadata.display_name}] {result.summary}"]
        if not result.success:
            lines.append("Status: FAILED")
        if result.errors:
            lines.extend(f"- {error}" for error in result.errors)
        return "\n".join(lines)
