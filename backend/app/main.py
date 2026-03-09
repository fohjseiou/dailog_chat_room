from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.logger import log
from app.api.v1 import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    log.info("application_started", port=settings.app_port)
    yield
    # Shutdown
    log.info("application_shutdown")


app = FastAPI(
    title="Legal Consultation API",
    version="0.1.0",
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
