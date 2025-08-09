from fastapi import APIRouter, HTTPException
from app.services.libvirt_client import list_vms, get_vm_info, vm_start, vm_shutdown, vm_destroy

router = APIRouter(prefix="/vms", tags=["vms"])

@router.get("/")
def get_vms():
    return {"vms": list_vms()}

@router.get("/{name}")
def get_vm(name: str):
    info = get_vm_info(name)
    if not info:
        raise HTTPException(status_code=404, detail=f"VM '{name}' not found")
    return info

@router.post("/{name}/start")
def start_vm(name: str):
    try:
        vm_start(name)
        return {"message": f"VM '{name}' started"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{name}/shutdown")
def shutdown_vm(name: str):
    try:
        vm_shutdown(name)
        return {"message": f"VM '{name}' shutdown signaled"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{name}/destroy")
def destroy_vm(name: str):
    try:
        vm_destroy(name)
        return {"message": f"VM '{name}' force-stopped"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
