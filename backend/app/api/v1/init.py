from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.services.init_service import InitializationService

router = APIRouter(prefix="/init", tags=["initialization"])

# Global initialization service instance
_init_service: Optional[InitializationService] = None


def get_init_service() -> InitializationService:
    global _init_service
    if _init_service is None:
        _init_service = InitializationService()
    return _init_service


class InitStatusResponse(BaseModel):
    overall_progress: float
    overall_status: str
    current_step: Optional[str]
    steps: dict
    error: Optional[str]


class InitStartRequest(BaseModel):
    pass


class InitializationStateResponse(BaseModel):
    overall_progress: float
    overall_status: str
    current_step: Optional[str]
    steps: dict
    error: Optional[str]


class InitStartResponse(BaseModel):
    message: str
    status: InitializationStateResponse


@router.get("/status", response_model=InitStatusResponse)
async def get_init_status(service: InitializationService = Depends(get_init_service)):
    """Get current initialization status."""
    return service.get_status_summary()


@router.post("/start", response_model=InitStartResponse)
async def start_initialization(
    request: InitStartRequest,
    service: InitializationService = Depends(get_init_service)
):
    """Start the initialization process."""
    if service.state.overall_status == "in_progress":
        return InitStartResponse(
            message="InicializaciÃ³n ya en progreso",
            status=service.get_status_summary()
        )
    
    # Run in background
    import asyncio
    asyncio.create_task(service.run())
    
    return InitStartResponse(
        message="InicializaciÃ³n iniciada",
        status=service.get_status_summary()
    )


@router.post("/cancel")
async def cancel_initialization(service: InitializationService = Depends(get_init_service)):
    """Cancel the initialization process."""
    service.cancel()
    return {"message": "InicializaciÃ³n cancelada", "status": service.get_status_summary()}


@router.post("/reset")
async def reset_initialization(service: InitializationService = Depends(get_init_service)):
    """Reset initialization state (for testing)."""
    global _init_service
    _init_service = InitializationService()
    return {"message": "Estado reiniciado", "status": _init_service.get_status_summary()}
