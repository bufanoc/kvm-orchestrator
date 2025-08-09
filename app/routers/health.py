
# Import the APIRouter class from FastAPI. APIRouter helps organize groups of related endpoints (routes).
from fastapi import APIRouter

# Create a router object. This will collect all the endpoints defined below so they can be included in the main app.
router = APIRouter()

# Define a GET endpoint at the root path ("/") of this router.
# The 'tags' argument is used for grouping endpoints in the API docs (Swagger UI).
@router.get("/", tags=["health"])
def root():
    # When someone visits this endpoint, return a simple message confirming the API is running.
    return {"message": "It works!"}

# Define a GET endpoint at "/status" for health checks.
# This is useful for monitoring if your API is up and running.
@router.get("/status", tags=["health"])
def status():
    # Return a status message indicating the service is healthy.
    return {"status": "healthy"}
