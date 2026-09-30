# Re-export del router admin desde app.admin.api
from app.admin.api import router

__all__ = ["router"]
