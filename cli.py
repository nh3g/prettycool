"""Command line entry point for PrettyCool."""
from __future__ import annotations

import argparse
from pathlib import Path

from app.config import settings_manager
from app.console import ConsoleEngine
from app.orchestrator import ModuleOrchestrator
from app.reporting import MarkdownBuilder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PrettyCool reconnaissance orchestrator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available modules")
    list_parser.add_argument("--category", help="Filter modules by category", default=None)

    run_parser = subparsers.add_parser("run", help="Execute modules")
    run_parser.add_argument("--target", required=True, help="Target domain or host")
    run_parser.add_argument(
        "--mode",
        choices=["module", "modules", "bundle", "all"],
        default="modules",
        help="Execution mode",
    )
    run_parser.add_argument("--modules", nargs="*", default=[], help="Modules to execute")
    run_parser.add_argument("--category", help="Category to execute when mode=bundle")

    console_parser = subparsers.add_parser("console", help="Execute a console command")
    console_parser.add_argument("console_cmd", help="Command to execute")

    return parser


def command_list(orchestrator: ModuleOrchestrator, category: str | None) -> None:
    modules = orchestrator.available_modules()
    if category:
        modules = [m for m in modules if m.category.lower() == category.lower()]
    for module in modules:
        print(f"- {module.name} ({module.category}) :: {module.description}")


def command_run(orchestrator: ModuleOrchestrator, args: argparse.Namespace) -> None:
    target: str = args.target
    mode: str = args.mode

    if mode == "module":
        if not args.modules:
            raise SystemExit("--modules is required when mode=module")
        modules = [args.modules[0]]
    elif mode == "modules":
        modules = args.modules
        if not modules:
            raise SystemExit("Provide at least one module when mode=modules")
    elif mode == "bundle":
        if not args.category:
            raise SystemExit("--category is required when mode=bundle")
        categories = orchestrator.categories()
        mapper = {key.lower(): key for key in categories}
        if args.category.lower() not in mapper:
            raise SystemExit("Unknown category")
        modules = [module.name for module in categories[mapper[args.category.lower()]]]
    else:  # all
        modules = [module.name for module in orchestrator.available_modules()]

    results = orchestrator.run_bundle(modules, target)
    builder = MarkdownBuilder(target, mode, results)
    path = Path("reports") / orchestrator.timestamped_report_name(target, mode)
    builder.save(path)
    for result in results:
        status = "SUCCESS" if result.success else "FAIL"
        print(f"[{status}] {result.metadata.display_name}: {result.summary}")
    print(f"Relatório salvo em {path}")


def command_console(engine: ConsoleEngine, command: str) -> None:
    response = engine.execute(command)
    prefix = "SUCCESS" if response.success else "ERROR"
    print(f"[{prefix}] {response.output}")
    if response.markdown_path:
        print(f"Relatório salvo em {response.markdown_path}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    orchestrator = ModuleOrchestrator(settings_manager)
    console_engine = ConsoleEngine(orchestrator)

    if args.command == "list":
        command_list(orchestrator, args.category)
    elif args.command == "run":
        command_run(orchestrator, args)
    elif args.command == "console":
        command_console(console_engine, args.console_cmd)


if __name__ == "__main__":
    main()
