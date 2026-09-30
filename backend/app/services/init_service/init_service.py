import asyncio
import json
import logging
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class InitializationStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class InitializationStep(str, Enum):
    CHECK_OLLAMA = "check_ollama"
    INSTALL_OLLAMA = "install_ollama"
    START_OLLAMA = "start_ollama"
    CHECK_MODELS = "check_models"
    DOWNLOAD_CHAT_MODEL = "download_chat_model"
    DOWNLOAD_EMBED_MODEL = "download_embed_model"
    VERIFY_BACKEND = "verify_backend"
    INIT_DATABASE = "init_database"
    COMPLETED = "completed"


@dataclass
class StepProgress:
    step: InitializationStep
    status: InitializationStatus = InitializationStatus.NOT_STARTED
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class InitializationState:
    steps: dict[InitializationStep, StepProgress] = field(default_factory=dict)
    overall_progress: float = 0.0
    overall_status: InitializationStatus = InitializationStatus.NOT_STARTED
    current_step: Optional[InitializationStep] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        for step in InitializationStep:
            self.steps[step] = StepProgress(step=step)


class InitializationService:
    """
    Handles first-run initialization:
    - Detects/installs Ollama
    - Downloads required models (phi3:3.8b, nomic-embed-text)
    - Verifies backend connectivity
    - Initializes database
    """
    
    REQUIRED_MODELS = {
        "chat": settings.ollama_chat_model,      # phi3:3.8b
        "embed": settings.ollama_embed_model,    # nomic-embed-text
    }
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(settings.qdrant_path).parent
        self.state = InitializationState()
        self._callbacks: list[Callable[[InitializationState], None]] = []
        self._cancelled = False
        
    def add_callback(self, callback: Callable[[InitializationState], None]) -> None:
        """Add a callback to receive progress updates."""
        self._callbacks.append(callback)
        
    def remove_callback(self, callback: Callable[[InitializationState], None]) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            
    def _notify(self) -> None:
        """Notify all callbacks of state change."""
        # Calculate overall progress
        total_steps = len([s for s in self.state.steps.values() 
                          if s.status != InitializationStatus.SKIPPED])
        completed = len([s for s in self.state.steps.values() 
                        if s.status == InitializationStatus.COMPLETED])
        self.state.overall_progress = completed / max(total_steps, 1)
        
        if self.state.overall_progress >= 1.0:
            self.state.overall_status = InitializationStatus.COMPLETED
            self.state.completed_at = datetime.utcnow()
            
        for callback in self._callbacks:
            try:
                callback(self.state)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def cancel(self) -> None:
        """Cancel the initialization process."""
        self._cancelled = True
        
    async def run(self) -> InitializationState:
        """Run the complete initialization sequence."""
        self.state.overall_status = InitializationStatus.IN_PROGRESS
        self.state.started_at = datetime.utcnow()
        self._notify()
        
        try:
            # Step 1: Check/Install Ollama
            await self._run_step(InitializationStep.CHECK_OLLAMA, self._check_ollama)
            if self._cancelled: return self.state
            
            if self.state.steps[InitializationStep.CHECK_OLLAMA].status == InitializationStatus.FAILED:
                await self._run_step(InitializationStep.INSTALL_OLLAMA, self._install_ollama)
                if self._cancelled: return self.state
                await self._run_step(InitializationStep.START_OLLAMA, self._start_ollama)
            
            # Step 2: Check/Download Models
            await self._run_step(InitializationStep.CHECK_MODELS, self._check_models)
            if self._cancelled: return self.state
            
            if self.state.steps[InitializationStep.CHECK_MODELS].status == InitializationStatus.FAILED:
                await self._run_step(InitializationStep.DOWNLOAD_CHAT_MODEL, 
                                   lambda: self._download_model("chat"))
                if self._cancelled: return self.state
                
                await self._run_step(InitializationStep.DOWNLOAD_EMBED_MODEL, 
                                   lambda: self._download_model("embed"))
            
            # Step 3: Verify Backend
            await self._run_step(InitializationStep.VERIFY_BACKEND, self._verify_backend)
            if self._cancelled: return self.state
            
            # Step 4: Initialize Database
            await self._run_step(InitializationStep.INIT_DATABASE, self._init_database)
            if self._cancelled: return self.state
            
            # Mark completed
            self.state.steps[InitializationStep.COMPLETED].status = InitializationStatus.COMPLETED
            self._notify()
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.state.overall_status = InitializationStatus.FAILED
            self.state.error = str(e)
            self._notify()
            
        return self.state
    
    async def _run_step(self, step: InitializationStep, func: Callable) -> None:
        """Run a single initialization step with progress tracking."""
        if self._cancelled:
            return
            
        step_progress = self.state.steps[step]
        step_progress.status = InitializationStatus.IN_PROGRESS
        step_progress.started_at = datetime.utcnow()
        step_progress.message = "Iniciando..."
        self.state.current_step = step
        self._notify()
        
        try:
            await func(step_progress)
            step_progress.status = InitializationStatus.COMPLETED
            step_progress.progress = 1.0
            step_progress.completed_at = datetime.utcnow()
            step_progress.message = "Completado"
        except Exception as e:
            logger.error(f"Step {step} failed: {e}")
            step_progress.status = InitializationStatus.FAILED
            step_progress.error = str(e)
            step_progress.message = f"Error: {e}"
            raise
        finally:
            self._notify()
    
    # Step implementations
    
    async def _check_ollama(self, progress: StepProgress) -> None:
        """Check if Ollama is installed and running."""
        progress.message = "Verificando Ollama..."
        progress.progress = 0.2
        self._notify()
        
        # Check if ollama command exists
        ollama_path = shutil.which("ollama")
        if not ollama_path:
            progress.message = "Ollama no encontrado"
            raise RuntimeError("Ollama no está instalado")
            
        progress.progress = 0.5
        self._notify()
        
        # Check if Ollama service is running
        try:
            proc = await asyncio.create_subprocess_exec(
                "ollama", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
            
            if proc.returncode != 0:
                raise RuntimeError(f"Ollama no responde: {stderr.decode()}")
                
        except asyncio.TimeoutError:
            raise RuntimeError("Ollama no responde (timeout)")
        except Exception as e:
            raise RuntimeError(f"Error conectando a Ollama: {e}")
            
        progress.progress = 1.0
        progress.message = "Ollama está funcionando"
    
    async def _install_ollama(self, progress: StepProgress) -> None:
        """Install Ollama using winget (Windows) or package manager."""
        system = platform.system().lower()
        
        progress.message = "Instalando Ollama..."
        progress.progress = 0.1
        self._notify()
        
        if system == "windows":
            # Use winget to install Ollama
            progress.message = "Descargando Ollama via winget..."
            progress.progress = 0.3
            self._notify()
            
            try:
                proc = await asyncio.create_subprocess_exec(
                    "winget", "install", "--id", "Ollama.Ollama", 
                    "--silent", "--accept-source-agreements", "--accept-package-agreements",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300.0)
                
                if proc.returncode != 0:
                    # Try alternative: download installer
                    progress.message = "Intentando instalador directo..."
                    progress.progress = 0.5
                    self._notify()
                    await self._install_ollama_direct(progress)
                    
            except asyncio.TimeoutError:
                raise RuntimeError("Timeout instalando Ollama (5 min)")
                
        elif system == "darwin":  # macOS
            progress.message = "Instalando Ollama via Homebrew..."
            progress.progress = 0.3
            self._notify()
            
            proc = await asyncio.create_subprocess_exec(
                "brew", "install", "ollama",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(proc.communicate(), timeout=300.0)
            
        else:  # Linux
            progress.message = "Instalando Ollama..."
            progress.progress = 0.3
            self._notify()
            
            proc = await asyncio.create_subprocess_exec(
                "curl", "-fsSL", "https://ollama.com/install.sh",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            
            if proc.returncode == 0:
                install_script = stdout.decode()
                proc = await asyncio.create_subprocess_shell(
                    install_script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await asyncio.wait_for(proc.communicate(), timeout=300.0)
        
        progress.progress = 1.0
        progress.message = "Ollama instalado correctamente"
    
    async def _install_ollama_direct(self, progress: StepProgress) -> None:
        """Direct download and install of Ollama on Windows."""
        import urllib.request
        import tempfile
        
        progress.message = "Descargando instalador de Ollama..."
        progress.progress = 0.5
        self._notify()
        
        url = "https://ollama.com/download/ollama-windows-amd64.exe"
        
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as tmp:
            tmp_path = tmp.name
            
        try:
            def progress_hook(block_num, block_size, total_size):
                if total_size > 0:
                    pct = min((block_num * block_size) / total_size, 1.0)
                    progress.progress = 0.5 + (pct * 0.3)
                    progress.message = f"Descargando Ollama: {pct:.0%}"
                    self._notify()
            
            urllib.request.urlretrieve(url, tmp_path, progress_hook)
            
            progress.message = "Instalando Ollama..."
            progress.progress = 0.8
            self._notify()
            
            proc = await asyncio.create_subprocess_exec(
                tmp_path, "/S",  # Silent install
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(proc.communicate(), timeout=300.0)
            
            if proc.returncode != 0:
                raise RuntimeError("Error instalando Ollama")
                
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except:
                pass
    
    async def _start_ollama(self, progress: StepProgress) -> None:
        """Start Ollama service."""
        progress.message = "Iniciando servicio Ollama..."
        progress.progress = 0.2
        self._notify()
        
        system = platform.system().lower()
        
        if system == "windows":
            # Start ollama serve in background
            try:
                # Try to start as service or background process
                proc = await asyncio.create_subprocess_exec(
                    "ollama", "serve",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
                )
                # Give it time to start
                await asyncio.sleep(3)
                
                # Verify it's running
                proc = await asyncio.create_subprocess_exec(
                    "ollama", "list",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await asyncio.wait_for(proc.communicate(), timeout=10.0)
                
            except Exception as e:
                raise RuntimeError(f"No se pudo iniciar Ollama: {e}")
                
        else:
            # Linux/macOS: systemctl or background
            pass
            
        progress.progress = 1.0
        progress.message = "Ollama iniciado"
    
    async def _check_models(self, progress: StepProgress) -> None:
        """Check if required models are available."""
        progress.message = "Verificando modelos..."
        progress.progress = 0.2
        self._notify()
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "ollama", "list", "--format", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
            
            if proc.returncode != 0:
                raise RuntimeError(f"Error listando modelos: {stderr.decode()}")
                
            models = json.loads(stdout.decode())
            model_names = {m.get("name", "") for m in models}
            
            missing = []
            for key, model in self.REQUIRED_MODELS.items():
                if model not in model_names:
                    missing.append((key, model))
                    
            if missing:
                missing_names = ", ".join([m[1] for m in missing])
                progress.message = f"Modelos faltantes: {missing_names}"
                raise RuntimeError(f"Modelos faltantes: {missing_names}")
                
            progress.progress = 1.0
            progress.message = "Todos los modelos disponibles"
            
        except Exception as e:
            raise RuntimeError(f"Error verificando modelos: {e}")
    
    async def _download_model(self, model_type: str) -> None:
        """Download a specific model."""
        model_name = self.REQUIRED_MODELS[model_type]
        
        async def _download(progress: StepProgress) -> None:
            progress.message = f"Descargando modelo {model_name}..."
            progress.progress = 0.1
            self._notify()
            
            proc = await asyncio.create_subprocess_exec(
                "ollama", "pull", model_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor progress via stderr
            while True:
                line = await proc.stderr.readline()
                if not line:
                    break
                line_str = line.decode().strip()
                if "pulling" in line_str.lower() or "%" in line_str:
                    # Parse progress if available
                    progress.message = f"Descargando {model_name}: {line_str}"
                    self._notify()
                    
            await proc.wait()
            
            if proc.returncode != 0:
                stderr = await proc.stderr.read()
                raise RuntimeError(f"Error descargando {model_name}: {stderr.decode()}")
                
            progress.progress = 1.0
            progress.message = f"Modelo {model_name} descargado"
            
        await self._run_step(
            InitializationStep.DOWNLOAD_CHAT_MODEL if model_type == "chat" 
            else InitializationStep.DOWNLOAD_EMBED_MODEL,
            _download
        )
    
    async def _verify_backend(self, progress: StepProgress) -> None:
        """Verify backend API is accessible."""
        progress.message = "Verificando backend..."
        progress.progress = 0.3
        self._notify()
        
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:8000/health")
                if response.status_code != 200:
                    raise RuntimeError(f"Backend no responde: {response.status_code}")
                    
        except Exception as e:
            raise RuntimeError(f"Backend no accesible: {e}")
            
        progress.progress = 1.0
        progress.message = "Backend verificado"
    
    async def _init_database(self, progress: StepProgress) -> None:
        """Initialize database (run migrations)."""
        progress.message = "Inicializando base de datos..."
        progress.progress = 0.3
        self._notify()
        
        # Run alembic migrations
        from app.database import init_db
        await init_db()
        
        progress.progress = 1.0
        progress.message = "Base de datos inicializada"
    
    def get_status_summary(self) -> dict:
        """Get a summary of initialization status for UI."""
        return {
            "overall_progress": self.state.overall_progress,
            "overall_status": self.state.overall_status.value,
            "current_step": self.state.current_step.value if self.state.current_step else None,
            "steps": {
                step.value: {
                    "status": progress.status.value,
                    "progress": progress.progress,
                    "message": progress.message,
                    "error": progress.error
                }
                for step, progress in self.state.steps.items()
            },
            "error": self.state.error
        }