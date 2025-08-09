from fastapi import FastAPI
from app.routers import health, vms

app = FastAPI(title="KVM Orchestrator")

app.include_router(health.router)
app.include_router(vms.router)
