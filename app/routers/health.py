from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["health"])
def root():
    return {"message": "It works!"}

@router.get("/status", tags=["health"])
def status():
    return {"status": "healthy"}
