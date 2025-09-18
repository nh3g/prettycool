"""Module orchestration layer."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List

from app.config import SettingsManager
from app.modules import MODULE_REGISTRY, ModuleExecutionError, ModuleMetadata, ModuleResult


class ModuleOrchestrator:
    """High level API that coordinates module execution."""

    def __init__(self, settings_manager: SettingsManager) -> None:
        self.settings_manager = settings_manager

    # ------------------------------------------------------------------
    def available_modules(self) -> List[ModuleMetadata]:
        """Return metadata for all registered modules."""

        return [module.metadata for module in MODULE_REGISTRY.values()]

    # ------------------------------------------------------------------
    def get_module(self, name: str):
        module_cls = MODULE_REGISTRY.get(name)
        if not module_cls:
            raise KeyError(f"Unknown module: {name}")
        # Always instantiate modules with the freshest configuration copy.
        return module_cls(self.settings_manager.settings)

    # ------------------------------------------------------------------
    def run_module(self, name: str, target: str, **options) -> ModuleResult:
        try:
            module = self.get_module(name)
        except KeyError:
            metadata = ModuleMetadata(
                name=name,
                display_name=f"Unregistered module: {name}",
                description="Module not found in the registry.",
                category="Unavailable",
            )
            message = f"Module '{name}' is not registered in the orchestrator."
            return ModuleResult(
                metadata=metadata,
                success=False,
                summary=message,
                errors=[message],
            )
        try:
            result = module.execute(target, **options)
            return result
        except ModuleExecutionError as exc:
            return ModuleResult(
                metadata=module.metadata,
                success=False,
                summary=str(exc),
                errors=[str(exc)],
            )
        except Exception as exc:  # pragma: no cover - defensive code
            return ModuleResult(
                metadata=module.metadata,
                success=False,
                summary="Unexpected error during module execution.",
                errors=[str(exc)],
            )

    # ------------------------------------------------------------------
    def run_bundle(self, modules: Iterable[str], target: str, **options) -> List[ModuleResult]:
        results: List[ModuleResult] = []
        for name in modules:
            results.append(self.run_module(name, target, **options))
        return results

    # ------------------------------------------------------------------
    def categories(self) -> Dict[str, List[ModuleMetadata]]:
        categorised: Dict[str, List[ModuleMetadata]] = {}
        for metadata in self.available_modules():
            categorised.setdefault(metadata.category, []).append(metadata)
        return categorised

    # ------------------------------------------------------------------
    def timestamped_report_name(self, target: str, mode: str) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        safe_target = target.replace("/", "-")
        return f"{timestamp}_{safe_target}_{mode}.md"
