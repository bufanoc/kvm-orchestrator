# Import the FastAPI class from the fastapi package. FastAPI is a modern web framework for building APIs with Python.
from fastapi import FastAPI
# Import the routers (collections of endpoints) for health and vms from the app.routers package.
from app.routers import health, vms, networks

# Create an instance of the FastAPI application.
# The 'title' argument sets the name that will appear in the API docs (Swagger UI).
app = FastAPI(title="KVM Orchestrator")

# Include the health router, which adds all endpoints defined in app/routers/health.py to the app.
app.include_router(health.router)
# Include the vms router, which adds all endpoints defined in app/routers/vms.py to the app.
app.include_router(vms.router)
# Include the networks router, which adds all endpoints defined in app/routers/networks.py to the app.
app.include_router(networks.router)
