import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from app.config import get_settings
from app.scheduler.jobs import check_overdue_allocations, update_booking_statuses

logger = logging.getLogger(__name__)

# Import all routers
from app.routers import (
    auth, departments, asset_categories, employees, assets,
    allocations, transfer_requests, bookings, maintenance_requests,
    audit, dashboard, reports, notifications, activity_logs,
)

settings = get_settings()
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle: start APScheduler on startup, shutdown on teardown."""
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Configure and start scheduler
    scheduler.add_job(
        check_overdue_allocations,
        "interval",
        hours=1,
        id="check_overdue_allocations",
    )
    scheduler.add_job(
        update_booking_statuses,
        "interval",
        minutes=5,
        id="update_booking_statuses",
    )
    scheduler.start()
    logger.info("Background scheduler started.")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("Background scheduler stopped.")


app = FastAPI(
    title="AssetFlow ONE",
    description="Enterprise Asset Management System — Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Serve uploaded files as static (HTML/JS/CSS blocked to prevent XSS)
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles as _StaticFiles

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

class SafeStaticFiles(_StaticFiles):
    """Static file server that blocks HTML/JS/CSS to prevent stored XSS."""
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if isinstance(response, FileResponse):
            media_type = response.media_type or ""
            if media_type in ("text/html", "application/javascript", "text/javascript", "text/css", "application/xhtml+xml"):
                from starlette.responses import Response
                return Response(status_code=403, content="Forbidden: this file type is not served")
        return response

app.mount("/uploads", SafeStaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Register all routers
app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(asset_categories.router)
app.include_router(employees.router)
app.include_router(assets.router)
app.include_router(allocations.router)
app.include_router(transfer_requests.router)
app.include_router(bookings.router)
app.include_router(maintenance_requests.router)
app.include_router(audit.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(notifications.router)
app.include_router(activity_logs.router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "AssetFlow ONE"}
