
# Import APIRouter and HTTPException from FastAPI. APIRouter helps organize endpoints, HTTPException is used for error responses.
# (FastAPI docs: https://fastapi.tiangolo.com/tutorial/bigger-applications/)
from fastapi import APIRouter, HTTPException 
# Import the CreateVm Pydantic model from app/models.py. This defines the expected structure for VM creation requests.
from app.models import CreateVm
# Import the create_vm function from app/services/vm_create.py. This handles the logic for creating a new VM.
from app.services.vm_create import create_vm
# Import functions for VM operations from app/services/libvirt_client.py. These handle VM lifecycle actions.
from app.services.libvirt_client import list_vms, get_vm_info, vm_start, vm_shutdown, vm_destroy


# Create a router for VM-related endpoints. All routes here will be prefixed with '/vms' and tagged as 'vms' in docs.
# (See FastAPI's APIRouter: https://fastapi.tiangolo.com/tutorial/bigger-applications/#apirouter)
router = APIRouter(prefix="/vms", tags=["vms"])


# List all virtual machines
# Calls list_vms() from app/services/libvirt_client.py
@router.get("/")
def get_vms():
    # Call the list_vms service function and return the result as JSON
    return {"vms": list_vms()}


# Get information about a specific VM by name
# Calls get_vm_info() from app/services/libvirt_client.py
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
# Calls vm_start() from app/services/libvirt_client.py
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
# Calls vm_shutdown() from app/services/libvirt_client.py
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
# Calls vm_destroy() from app/services/libvirt_client.py
@router.post("/{name}/destroy")
def destroy_vm(name: str):
    try:
        # Try to force-stop the VM using the service function
        vm_destroy(name)
        return {"message": f"VM '{name}' force-stopped"}
    except Exception as e:
        # If something goes wrong, return a 400 error with the error message
        raise HTTPException(status_code=400, detail=str(e))

# Create a new VM using the provided specification
# This endpoint expects a JSON body matching the CreateVm model (see app/models.py)
# Calls create_vm() from app/services/vm_create.py
@router.post("/")
def create_vm_endpoint(spec: CreateVm):
    create_vm(
        name=spec.name,           # VM name (string)
        vcpus=spec.vcpus,         # Number of virtual CPUs (int)
        memory_mb=spec.memory_mb, # Memory in MB (int)
        disk_gb=spec.disk_gb,     # Disk size in GB (int)
        network=spec.network,     # Network name or config (string)
        ssh_pubkey=spec.ssh_pubkey, # SSH public key (string, see app/models.py for usage)
    )
    return {"message": f"VM '{spec.name}' created"}
