
# Import APIRouter and HTTPException from FastAPI. APIRouter helps organize endpoints, HTTPException is used for error responses.
from fastapi import APIRouter, HTTPException
# Import functions for VM operations from the service layer.
from app.services.libvirt_client import list_vms, get_vm_info, vm_start, vm_shutdown, vm_destroy

# Create a router for VM-related endpoints. All routes here will be prefixed with '/vms' and tagged as 'vms' in docs.
router = APIRouter(prefix="/vms", tags=["vms"])

# List all virtual machines
@router.get("/")
def get_vms():
    # Call the list_vms service function and return the result as JSON
    return {"vms": list_vms()}

# Get information about a specific VM by name
@router.get("/{name}")
def get_vm(name: str):
    # Call the get_vm_info service function
    info = get_vm_info(name)
    if not info:
        # If the VM is not found, return a 404 error
        raise HTTPException(status_code=404, detail=f"VM '{name}' not found")
    # Return the VM's information
    return info

# Start a specific VM by name
@router.post("/{name}/start")
def start_vm(name: str):
    try:
        # Try to start the VM using the service function
        vm_start(name)
        return {"message": f"VM '{name}' started"}
    except Exception as e:
        # If something goes wrong, return a 400 error with the error message
        raise HTTPException(status_code=400, detail=str(e))

# Gracefully shut down a specific VM by name
@router.post("/{name}/shutdown")
def shutdown_vm(name: str):
    try:
        # Try to shut down the VM using the service function
        vm_shutdown(name)
        return {"message": f"VM '{name}' shutdown signaled"}
    except Exception as e:
        # If something goes wrong, return a 400 error with the error message
        raise HTTPException(status_code=400, detail=str(e))

# Force-stop (destroy) a specific VM by name
@router.post("/{name}/destroy")
def destroy_vm(name: str):
    try:
        # Try to force-stop the VM using the service function
        vm_destroy(name)
        return {"message": f"VM '{name}' force-stopped"}
    except Exception as e:
        # If something goes wrong, return a 400 error with the error message
        raise HTTPException(status_code=400, detail=str(e))
