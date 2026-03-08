from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.logger import log

settings = get_settings()

app = FastAPI(
    title="Legal Consultation API",
    version="0.1.0",
    debug=settings.app_debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    log.info("application_started", port=settings.app_port)


@app.on_event("shutdown")
async def shutdown_event():
    log.info("application_shutdown")
