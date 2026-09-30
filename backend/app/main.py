from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import structlog

from app.multi_tenancy.middleware import TenantMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.api.v1 import auth, emails, tasks, projects, ai, notifications, followups, health, calendar, commitments, deadlines, search, blockers, workmap, connectors, admin, init
from app.services.scheduler_service import SchedulerService

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logging.basicConfig(level=settings.log_level.upper())

scheduler_service = SchedulerService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    scheduler_service.start()
    yield
    # Shutdown
    scheduler_service.stop()
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TenantMiddleware)

# Include routers
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(emails.router, prefix=settings.api_prefix)
app.include_router(tasks.router, prefix=settings.api_prefix)
app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(ai.router, prefix=settings.api_prefix)
app.include_router(notifications.router, prefix=settings.api_prefix)
app.include_router(followups.router, prefix=settings.api_prefix)
app.include_router(calendar.router, prefix=settings.api_prefix)
app.include_router(commitments.router, prefix=settings.api_prefix)
app.include_router(deadlines.router, prefix=settings.api_prefix)
app.include_router(search.router, prefix=settings.api_prefix)
app.include_router(blockers.router, prefix=settings.api_prefix)
app.include_router(workmap.router, prefix=settings.api_prefix)
app.include_router(connectors.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
app.include_router(init.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    return {"name": settings.app_name, "version": "0.1.0", "status": "running"}