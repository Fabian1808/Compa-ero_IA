from dataclasses import asdict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel

from app.api.v1.deps import get_optional_user_id, require_local_client
from app.services.installer_service import (
    DependencyStatus,
    first_run_marker,
    installer_service,
)

router = APIRouter(prefix="/installer", tags=["installer"])


class DependencyStatusResponse(BaseModel):
    name: str
    installed: bool
    version: str | None = None
    required_version: str | None = None
    description: str = ""
    install_url: str | None = None
    auto_installable: bool = False


class InstallProgressResponse(BaseModel):
    step: str
    progress: int
    message: str
    details: str | None = None
    completed: bool = False
    error: str | None = None


class InstallRequest(BaseModel):
    dependencies: list[str] | None = None  # If None, install all missing


class InstallResponse(BaseModel):
    success: bool
    code: str
    progress: InstallProgressResponse


def _status_payload(deps: dict[str, DependencyStatus]) -> dict[str, DependencyStatusResponse]:
    return {name: DependencyStatusResponse(**asdict(dep)) for name, dep in deps.items()}


@router.get("/status", response_model=dict[str, DependencyStatusResponse])
async def get_installer_status(_: None = Depends(require_local_client)):
    """Report which required components are present on this computer."""
    deps = await installer_service.check_all_dependencies()
    return _status_payload(deps)


@router.get("/progress", response_model=InstallProgressResponse)
async def get_install_progress(_: None = Depends(require_local_client)):
    """Return the progress of the installation currently running."""
    return InstallProgressResponse(**asdict(installer_service.get_progress()))


@router.post("/check", response_model=dict[str, DependencyStatusResponse])
async def check_dependencies(_: None = Depends(require_local_client)):
    """Re-check every required component."""
    deps = await installer_service.check_all_dependencies()
    return _status_payload(deps)


@router.post("/install", response_model=InstallResponse)
async def install_dependencies(
    request: InstallRequest,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_local_client),
):
    """Install the components that are missing."""
    deps = await installer_service.check_all_dependencies()

    to_install = request.dependencies
    if to_install is None:
        to_install = [
            name for name, dep in deps.items() if not dep.installed and dep.auto_installable
        ]

    if not to_install:
        return InstallResponse(
            success=True,
            code="installer.alreadyInstalled",
            progress=InstallProgressResponse(
                step="complete", progress=100, message="installer.stepComplete", completed=True
            ),
        )

    selected = {name: deps[name] for name in to_install if name in deps}

    async def run_install() -> None:
        await installer_service.install_all_missing(selected)

    background_tasks.add_task(run_install)

    return InstallResponse(
        success=True,
        code="installer.started",
        progress=InstallProgressResponse(
            step="starting", progress=0, message="installer.stepStarting"
        ),
    )


@router.post("/install/ollama")
async def install_ollama(
    background_tasks: BackgroundTasks,
    _: None = Depends(require_local_client),
):
    """Install the local AI engine."""

    async def run_install() -> None:
        await installer_service.install_ollama()

    background_tasks.add_task(run_install)
    return {"success": True, "code": "installer.engineInstallStarted"}


@router.post("/install/model/{model_name}")
async def install_model(
    model_name: str,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_local_client),
):
    """Download a specific model."""

    async def run_install() -> None:
        await installer_service.pull_model(model_name)

    background_tasks.add_task(run_install)
    return {"success": True, "code": "installer.modelDownloadStarted"}


@router.post("/initialize")
async def initialize_first_run(
    background_tasks: BackgroundTasks,
    _: None = Depends(require_local_client),
):
    """Run the complete first-run installation."""

    async def run_init() -> None:
        await installer_service.run_first_run()

    background_tasks.add_task(run_init)
    return {"success": True, "code": "installer.firstRunStarted"}


@router.get("/first-run-needed")
async def check_first_run_needed(
    request: Request,
    user_id: str | None = Depends(get_optional_user_id),
):
    """
    Report whether the first-run setup still needs to happen.

    This runs before any account is connected, so a missing user is a normal
    state rather than an error: it simply means setup has not finished yet.
    """
    if user_id is None:
        return {
            "first_run_needed": not first_run_marker.exists(),
            "code": "installer.noAccountYet",
        }

    return {
        "first_run_needed": not first_run_marker.exists(),
        "code": "installer.checkComplete",
    }


@router.post("/mark-initialized")
async def mark_initialized(_: None = Depends(require_local_client)):
    """
    Record that first-run setup finished.

    Stored as a marker in the local data folder rather than on the user record,
    because it must succeed before an account exists.
    """
    if not first_run_marker.create():
        raise HTTPException(
            status_code=500,
            detail="Setup could not be recorded on this computer.",
        )
    return {"success": True, "code": "installer.setupCompleted"}
