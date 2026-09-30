import asyncio
import hashlib
import logging
import os
import platform
import re
import shutil
import subprocess
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

# Stable identifiers the UI translates into the user's language.
# The backend never sends prose: it sends a code, so the wording lives in one
# place per locale instead of being duplicated across Python and TypeScript.
STEP_CHECKING = "installer.stepChecking"
STEP_CHECK_COMPLETE = "installer.stepCheckComplete"
STEP_STARTING = "installer.stepStarting"
STEP_COMPLETE = "installer.stepComplete"

CODE_NO_ACCOUNT = "installer.noAccountYet"
CODE_CHECK_COMPLETE = "installer.checkComplete"
CODE_ALREADY_INSTALLED = "installer.alreadyInstalled"
CODE_STARTED = "installer.started"
CODE_ENGINE_INSTALL_STARTED = "installer.engineInstallStarted"
CODE_MODEL_DOWNLOAD_STARTED = "installer.modelDownloadStarted"
CODE_FIRST_RUN_STARTED = "installer.firstRunStarted"
CODE_SETUP_COMPLETED = "installer.setupCompleted"


@dataclass
class DependencyStatus:
    name: str
    installed: bool
    version: str | None = None
    required_version: str | None = None
    description: str = ""
    install_url: str | None = None
    auto_installable: bool = False


@dataclass
class InstallProgress:
    step: str
    progress: int  # 0-100
    message: str
    details: str | None = None
    completed: bool = False
    error: str | None = None


class FirstRunMarker:
    """
    Records that first-run setup finished.

    A file in the app's own data folder is used rather than a column on the user
    record, because setup must be able to complete before any Microsoft account
    is connected.
    """

    def __init__(self, data_dir: Path) -> None:
        self._path = data_dir / "config" / "first-run.json"

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._path.exists()

    def create(self) -> bool:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                '{"completed": true}\n',
                encoding="utf-8",
            )
            return True
        except OSError as exc:
            logger.error("Could not record first-run completion: %s", exc)
            return False

    def clear(self) -> bool:
        try:
            self._path.unlink(missing_ok=True)
            return True
        except OSError as exc:
            logger.error("Could not clear first-run marker: %s", exc)
            return False


class InstallerService:
    def __init__(self) -> None:
        self.data_dir = Path(settings.data_dir)
        self.ollama_dir = self.data_dir / "ai" / "ollama"
        self.models_dir = self.data_dir / "ai" / "models"
        self._progress_callback: Callable[[InstallProgress], None] | None = None
        self._current_progress = InstallProgress(step="", progress=0, message=STEP_STARTING)

    def set_progress_callback(self, callback: Callable[[InstallProgress], None]) -> None:
        self._progress_callback = callback

    def _update_progress(
        self,
        step: str,
        progress: int,
        message: str,
        details: str | None = None,
        completed: bool = False,
        error: str | None = None,
    ) -> None:
        self._current_progress = InstallProgress(
            step=step,
            progress=progress,
            message=message,
            details=details,
            completed=completed,
            error=error,
        )
        if self._progress_callback:
            self._progress_callback(self._current_progress)

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------
    async def check_all_dependencies(self) -> dict[str, DependencyStatus]:
        """Report which required components are present."""
        self._update_progress("check", 10, STEP_CHECKING)

        deps: dict[str, DependencyStatus] = {
            "data_dir": self._check_data_dir(),
            "ollama": await self.check_engine(),
            "phi3": await self._check_model(settings.ollama_chat_model),
            "nomic-embed": await self._check_model(settings.ollama_embed_model),
        }

        # The database can only exist once its folder does, so it is reported
        # after the folder rather than being listed before it.
        deps["database"] = self._check_database()
        deps = dict(sorted(deps.items(), key=_dependency_sort_key))

        self._update_progress("check", 100, STEP_CHECK_COMPLETE, completed=True)
        return deps

    def _check_data_dir(self) -> DependencyStatus:
        return DependencyStatus(
            name="data_dir",
            installed=self.data_dir.exists(),
            auto_installable=True,
        )

    def _check_database(self) -> DependencyStatus:
        db_path = Path(settings.database_url.replace("sqlite+aiosqlite:///", ""))
        return DependencyStatus(
            name="database",
            installed=db_path.exists(),
            auto_installable=True,
        )

    async def check_engine(self) -> DependencyStatus:
        """Check whether the local AI engine is installed."""
        engine_path = self._find_engine()
        if not engine_path:
            return DependencyStatus(
                name="ollama",
                installed=False,
                auto_installable=self._engine_install_allowed(),
            )

        version = await self._engine_version(engine_path)
        return DependencyStatus(
            name="ollama",
            installed=True,
            version=version,
            required_version="0.1.0",
            auto_installable=False,
        )

    def _engine_install_allowed(self) -> bool:
        """
        Auto-install is only offered when the download can be verified.

        Without a pinned SHA-256 the installer refuses to run an unverified
        binary, so the component is reported as manual-only instead.
        """
        if platform.system() == "Windows":
            return bool(settings.ollama_installer_sha256.strip())
        return True

    def _find_engine(self) -> str | None:
        found = shutil.which("ollama")
        if found:
            return found

        if platform.system() == "Windows":
            candidates = [
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
                Path(os.environ.get("PROGRAMFILES", "")) / "Ollama" / "ollama.exe",
                self.ollama_dir / "ollama.exe",
            ]
            for candidate in candidates:
                if candidate.exists():
                    return str(candidate)

        return None

    async def _engine_version(self, engine_path: str) -> str:
        try:
            process = await asyncio.create_subprocess_exec(
                engine_path,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            return stdout.decode(errors="replace").strip() or "unknown"
        except OSError as exc:
            logger.warning("Could not read engine version: %s", exc)
            return "unknown"

    async def engine_is_running(self) -> bool:
        """Check whether the local engine is answering."""
        try:
            import aiohttp

            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{settings.ollama_base_url}/api/tags", timeout=timeout
                ) as response:
                    return response.status == 200
        except Exception:
            return False

    async def _check_model(self, model_name: str) -> DependencyStatus:
        """Check whether a model is already available locally."""
        try:
            import aiohttp

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{settings.ollama_base_url}/api/tags", timeout=timeout
                ) as response:
                    if response.status == 200:
                        payload = await response.json()
                        family = model_name.split(":")[0]
                        for model in payload.get("models", []):
                            if str(model.get("name", "")).startswith(family):
                                return DependencyStatus(
                                    name=model_name,
                                    installed=True,
                                    version=str(model.get("size", "unknown")),
                                    auto_installable=False,
                                )
        except Exception:
            pass

        return DependencyStatus(name=model_name, installed=False, auto_installable=True)

    # ------------------------------------------------------------------
    # Installation
    # ------------------------------------------------------------------
    async def install_all_missing(self, deps: dict[str, DependencyStatus]) -> bool:
        """Install every requested component that is not present yet."""
        missing = [name for name, dep in deps.items() if not dep.installed and dep.auto_installable]

        if not missing:
            self._update_progress("install", 100, STEP_COMPLETE, completed=True)
            return True

        total_steps = len(missing)
        for index, name in enumerate(missing):
            progress = int((index / total_steps) * 100)
            self._update_progress("install", progress, "installer.stepInstallingComponent")

            if not await self._install_dependency(name):
                self._update_progress(
                    "install",
                    progress,
                    "installer.stepComponentFailed",
                    error=f"installer.componentFailed:{name}",
                )
                return False

        self._update_progress("install", 100, STEP_COMPLETE, completed=True)
        return True

    async def run_first_run(self) -> bool:
        """Run the whole first-run installation in dependency order."""
        # The folder must exist before anything can be written into it.
        if not await self._create_data_dir():
            return False

        if not self._check_database().installed:
            await self._init_database()

        if not (await self.check_engine()).installed:
            if not await self.install_engine():
                return False

        for model in (settings.ollama_chat_model, settings.ollama_embed_model):
            status = await self._check_model(model)
            if not status.installed:
                if not await self.pull_model(model):
                    return False

        self._update_progress("install", 100, STEP_COMPLETE, completed=True)
        return True

    async def _install_dependency(self, dep_name: str) -> bool:
        try:
            if dep_name == "data_dir":
                return await self._create_data_dir()
            if dep_name == "database":
                return await self._init_database()
            if dep_name == "ollama":
                return await self.install_engine()
            if dep_name == "phi3":
                return await self.pull_model(settings.ollama_chat_model)
            if dep_name == "nomic-embed":
                return await self.pull_model(settings.ollama_embed_model)
            return False
        except Exception as exc:
            logger.error("Error installing %s: %s", dep_name, exc)
            return False

    async def _create_data_dir(self) -> bool:
        """Create the folder structure the app stores data in."""
        directories = [
            self.data_dir,
            self.data_dir / "database",
            self.data_dir / "ai" / "models",
            self.data_dir / "ai" / "embeddings",
            self.data_dir / "cache",
            self.data_dir / "logs",
            self.data_dir / "config",
            self.data_dir / "attachments",
            self.ollama_dir,
            self.models_dir,
        ]
        try:
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
            return True
        except OSError as exc:
            logger.error("Error creating data folder: %s", exc)
            return False

    async def _init_database(self) -> bool:
        """
        Prepare the database location.

        The schema itself is created by the application on startup through
        Alembic; this only makes sure the folder is ready to receive it.
        """
        try:
            Path(settings.database_url.replace("sqlite+aiosqlite:///", "")).parent.mkdir(
                parents=True, exist_ok=True
            )
            return True
        except OSError as exc:
            logger.error("Error preparing database folder: %s", exc)
            return False

    async def install_engine(self) -> bool:
        """Download and install the local AI engine."""
        if platform.system() == "Windows":
            return await self._install_engine_windows()
        return await self._install_engine_unix()

    async def _install_engine_windows(self) -> bool:
        expected_digest = settings.ollama_installer_sha256.strip().lower()
        if not expected_digest:
            # Fail closed: never execute a download that cannot be verified.
            logger.error("Refusing to install: no pinned SHA-256 for the installer")
            self._update_progress(
                "install",
                30,
                "installer.stepUnverifiedDownload",
                error="installer.errorUnverifiedDownload",
            )
            return False

        self._update_progress("install", 20, "installer.stepDownloadingEngine")
        installer_path = self.data_dir / "cache" / "OllamaSetup.exe"

        try:
            installer_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error("Could not prepare cache folder: %s", exc)
            return False

        try:
            # Runs off the event loop so the server stays responsive during a
            # multi-hundred-megabyte download.
            await asyncio.to_thread(
                _download_with_progress, OLLAMA_WINDOWS_INSTALLER_URL, installer_path, self
            )
        except Exception as exc:
            logger.error("Engine download failed: %s", exc)
            self._update_progress(
                "install", 30, "installer.stepDownloadFailed", error="installer.errorDownloadFailed"
            )
            return False

        digest = await asyncio.to_thread(_sha256_file, installer_path)
        if digest != expected_digest:
            logger.error(
                "Engine installer digest mismatch: expected %s, got %s", expected_digest, digest
            )
            installer_path.unlink(missing_ok=True)
            self._update_progress(
                "install",
                30,
                "installer.stepIntegrityFailed",
                error="installer.errorIntegrityFailed",
            )
            return False

        self._update_progress("install", 60, "installer.stepInstallingEngine")
        try:
            process = await asyncio.create_subprocess_exec(
                str(installer_path),
                "/S",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=_no_window_flag(),
            )
            await process.communicate()
        except OSError as exc:
            logger.error("Could not run engine installer: %s", exc)
            return False

        if process.returncode != 0:
            logger.error("Engine installer exited with %s", process.returncode)
            return False

        installer_path.unlink(missing_ok=True)

        await asyncio.sleep(2)
        if not self._find_engine():
            logger.error("Engine not found after installation")
            return False

        self._update_progress("install", 80, "installer.stepStartingEngine")
        return await self.start_engine()

    async def _install_engine_unix(self) -> bool:
        self._update_progress("install", 30, "installer.stepInstallingEngine")
        script_path = self.data_dir / "cache" / "ollama-install.sh"

        try:
            script_path.parent.mkdir(parents=True, exist_ok=True)
            # The official script is downloaded first and reviewed on disk
            # instead of being piped straight into a shell, so nothing runs
            # that was not actually fetched from the vendor's URL.
            await asyncio.to_thread(
                _download_to_path, OLLAMA_UNIX_INSTALLER_URL, script_path
            )
            process = await asyncio.create_subprocess_exec(
                "sh", str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await process.communicate()
        except OSError as exc:
            logger.error("Could not run engine installer: %s", exc)
            return False

        if process.returncode != 0:
            logger.error("Engine installer failed: %s", stderr.decode(errors="replace"))
            return False

        script_path.unlink(missing_ok=True)
        return await self.start_engine()

    async def start_engine(self) -> bool:
        """Start the engine and wait for it to answer."""
        engine_path = self._find_engine() or "ollama"
        try:
            await asyncio.create_subprocess_exec(
                engine_path,
                "serve",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                creationflags=_no_window_flag(),
            )
        except OSError as exc:
            logger.error("Could not start engine: %s", exc)
            return False

        for _ in range(30):
            await asyncio.sleep(1)
            if await self.engine_is_running():
                return True

        return False

    async def pull_model(self, model_name: str) -> bool:
        """Download a model into the local engine."""
        self._update_progress("install", 50, "installer.stepDownloadingModel")

        engine_path = self._find_engine()
        if not engine_path:
            logger.error("Cannot download a model before the engine is installed")
            return False

        try:
            process = await asyncio.create_subprocess_exec(
                engine_path,
                "pull",
                model_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=_no_window_flag(),
            )
        except OSError as exc:
            logger.error("Could not start model download: %s", exc)
            return False

        await self._report_pull_progress(process)
        returncode = await process.wait()

        if returncode != 0:
            stderr = await process.stderr.read()
            logger.error("Model download failed: %s", stderr.decode(errors="replace"))
            self._update_progress(
                "install", 50, "installer.stepDownloadFailed", error="installer.errorModelFailed"
            )
            return False

        self._update_progress("install", 100, STEP_COMPLETE, completed=True)
        return True

    async def _report_pull_progress(self, process) -> None:
        """
        Surface download progress.

        The engine writes its progress to stderr, not stdout, so both streams are
        drained. Without this the pipe fills and the download stalls.
        """
        percent_pattern = re.compile(rb"(\d+)%")
        last_percent = -1

        async def handle(line: bytes) -> None:
            nonlocal last_percent
            match = percent_pattern.search(line)
            if not match:
                return
            percent = int(match.group(1))
            if percent != last_percent:
                last_percent = percent
                self._update_progress(
                    "install", 50 + percent // 2, "installer.stepDownloadingModel"
                )

        async def drain(stream) -> None:
            while True:
                line = await stream.readline()
                if not line:
                    return
                await handle(line)

        await asyncio.gather(drain(process.stdout), drain(process.stderr))

    def get_progress(self) -> InstallProgress:
        return self._current_progress


OLLAMA_WINDOWS_INSTALLER_URL = "https://ollama.com/download/OllamaSetup.exe"
OLLAMA_UNIX_INSTALLER_URL = "https://ollama.com/install.sh"

_INSTALL_ORDER = ["data_dir", "database", "ollama", "phi3", "nomic-embed"]


def _dependency_sort_key(item: str) -> int:
    try:
        return _INSTALL_ORDER.index(item)
    except ValueError:
        return len(_INSTALL_ORDER)


def _no_window_flag() -> int:
    """Keeps installer windows from flashing on screen."""
    if platform.system() == "Windows":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_to_path(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310 - pinned vendor URL
        with destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)


def _download_with_progress(url: str, destination: Path, service: "InstallerService") -> None:
    with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310 - pinned vendor URL
        total = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        with destination.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                handle.write(chunk)
                downloaded += len(chunk)
                if total:
                    percent = min(100, int(downloaded * 100 / total))
                    service._update_progress(
                        "install", 30 + percent // 3, "installer.stepDownloadingEngine"
                    )


installer_service = InstallerService()
first_run_marker = FirstRunMarker(Path(settings.data_dir))
