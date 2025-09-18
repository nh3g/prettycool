"""FastAPI entrypoint for the PrettyCool web interface."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.config import settings_manager
from app.console import ConsoleEngine
from app.orchestrator import ModuleOrchestrator
from app.reporting import MarkdownBuilder

app = FastAPI(title="PrettyCool Control Center", version="2.0.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

orchestrator = ModuleOrchestrator(settings_manager)
console_engine = ConsoleEngine(orchestrator)
REPORTS_DIR = Path("reports")


class RunRequest(BaseModel):
    target: str
    modules: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    mode: Literal["module", "modules", "bundle", "all"] = "module"
    options: Dict[str, str] = Field(default_factory=dict)


class ConsoleRequest(BaseModel):
    command: str


class APIKeysUpdate(BaseModel):
    keys: Dict[str, Optional[str]] = Field(default_factory=dict)
    timeout: Optional[int] = None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/modules")
def list_modules() -> Dict[str, List[Dict[str, str]]]:
    modules = orchestrator.available_modules()
    response = [
        {
            "name": module.name,
            "display_name": module.display_name,
            "description": module.description,
            "category": module.category,
            "requires_api_keys": list(module.requires_api_keys),
            "documentation_url": module.documentation_url,
        }
        for module in modules
    ]
    return {"modules": response}


@app.post("/api/run")
def run_modules(request: RunRequest):
    if request.mode == "module":
        if not request.modules:
            raise HTTPException(status_code=400, detail="Module name is required when mode is 'module'.")
        module_name = request.modules[0]
        _validate_modules([module_name])
        result = orchestrator.run_module(module_name, request.target, **request.options)
        results = [result]
        mode_label = f"module-{module_name}"
    elif request.mode == "modules":
        if not request.modules:
            raise HTTPException(status_code=400, detail="Provide at least one module to execute.")
        _validate_modules(request.modules)
        results = orchestrator.run_bundle(request.modules, request.target, **request.options)
        mode_label = "selected"
    elif request.mode == "bundle":
        if not request.category:
            raise HTTPException(status_code=400, detail="Category name is required for bundle execution.")
        categories = orchestrator.categories()
        matched = {key.lower(): key for key in categories}
        key = request.category.lower()
        if key not in matched:
            raise HTTPException(status_code=404, detail="Unknown module category.")
        modules = [module.name for module in categories[matched[key]]]
        results = orchestrator.run_bundle(modules, request.target, **request.options)
        mode_label = f"bundle-{matched[key]}"
    elif request.mode == "all":
        modules = [module.name for module in orchestrator.available_modules()]
        results = orchestrator.run_bundle(modules, request.target, **request.options)
        mode_label = "full"
    else:  # pragma: no cover - safety
        raise HTTPException(status_code=400, detail="Invalid mode provided.")

    report_builder = MarkdownBuilder(request.target, mode_label, results)
    report_path = REPORTS_DIR / orchestrator.timestamped_report_name(request.target, mode_label)
    report_builder.save(report_path)

    return {
        "results": [serialize_result(result) for result in results],
        "report_path": str(report_path),
    }


@app.post("/api/modules/{module_name}/execute")
def run_single_module(module_name: str, request: RunRequest):
    payload = RunRequest(target=request.target, modules=[module_name], options=request.options)
    return run_modules(payload)


@app.get("/api/config/keys")
def get_api_keys():
    settings = settings_manager.settings
    key_dump = {}
    for name, value in settings.api_keys.model_dump().items():
        key_dump[name] = {
            "set": bool(value),
            "value": value[-4:] if value else "",
        }
    return {"keys": key_dump, "timeout": settings.request_timeout}


@app.put("/api/config/keys")
def update_api_keys(payload: APIKeysUpdate):
    if payload.keys:
        settings_manager.update_api_keys(payload.keys)
    if payload.timeout is not None:
        settings_manager.update_timeout(payload.timeout)
    return get_api_keys()


@app.post("/api/console")
def execute_console(request: ConsoleRequest):
    response = console_engine.execute(request.command)
    return {
        "success": response.success,
        "output": response.output,
        "report_path": response.markdown_path,
    }


def _validate_modules(module_names: List[str]) -> None:
    if not module_names:
        return
    available = {metadata.name for metadata in orchestrator.available_modules()}
    invalid = sorted({name for name in module_names if name not in available})
    if invalid:
        joined = ", ".join(invalid)
        raise HTTPException(status_code=404, detail=f"Unknown module(s): {joined}")


def serialize_result(result) -> Dict[str, object]:
    return {
        "module": result.metadata.name,
        "display_name": result.metadata.display_name,
        "category": result.metadata.category,
        "success": result.success,
        "summary": result.summary,
        "records": result.records,
        "errors": result.errors,
    }
