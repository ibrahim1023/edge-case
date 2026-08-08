from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from edgecase.api import (
    analyze,
    config,
    explain,
    findings,
    implement,
    preferences,
    repository,
    session,
    status,
    webhooks,
)

app = FastAPI(
    title="EdgeCase",
    description="Voice-first AI agent that discovers the most important missing pytest scenarios in public Python GitHub repositories.",
    version="0.1.0",
)

app.include_router(config.router)
app.include_router(session.router)
app.include_router(repository.router)
app.include_router(preferences.router)
app.include_router(analyze.router)
app.include_router(status.router)
app.include_router(findings.router)
app.include_router(explain.router)
app.include_router(implement.router)
app.include_router(webhooks.router)

static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
