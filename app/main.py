from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings 
from app.api import endpoints

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s -%(levelname)s -%(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description = "Event-driven notification system (Phase 1)",
    version= "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers = ["*"],
)

app.include_router(endpoints.router)

@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
)

async def health_check() -> dict:
    return {"status": "healthy"}


@app.get(
    "/",
    tags=["root"],
    summary="API documentation",
)

async def root() -> dict:
    return {
        "message": "Event Notification System (Phase 1)",
        "docs": "/docs",
        "health": "/health",
    }


@app.on_event("startup")
async def startup_event():
    logger.info(f"starting {settings.app_name}")
    logger.info(f"Debug mode: {settings.debug}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.app_name}")

    