# Import FastAPI's APIRouter for organizing endpoints and HTTPException for error handling.
# (FastAPI docs: https://fastapi.tiangolo.com/tutorial/bigger-applications/)
from fastapi import APIRouter, HTTPException
# Import the CreateVm model (defines the expected structure for VM creation requests) from app/models.py.
from app.models import CreateVm
# Import the create_vm function (handles VM creation logic) from app/services/vm_create.py.
from app.services.vm_create import create_vm
# Import VM lifecycle functions from app/services/libvirt_client.py.
from app.services.libvirt_client import (
    list_vms, get_vm_info, vm_start, vm_shutdown, vm_destroy, vm_delete,
    get_vm_macs,  # <- added 08112025
)


import subprocess, re, time # Added on 08102025

# Create a router for all VM-related endpoints. All routes here will be prefixed with '/vms' and tagged as 'vms' in docs.
router = APIRouter(prefix="/vms", tags=["vms"])



# List all virtual machines.
# Calls list_vms() from app/services/libvirt_client.py and returns a JSON list of VMs.
@router.get("/")
def get_vms():
    return {"vms": list_vms()}



# Get information about a specific VM by name.
# Calls get_vm_info() from app/services/libvirt_client.py.
@router.get("/{name}")
def get_vm(name: str):
    info = get_vm_info(name)
    if not info:
        # If the VM is not found, return a 404 error.
        raise HTTPException(status_code=404, detail=f"VM '{name}' not found")
    return info



# Start a specific VM by name.
# Calls vm_start() from app/services/libvirt_client.py.
@router.post("/{name}/start")
def start_vm(name: str):
    try:
        vm_start(name)
        return {"message": f"VM '{name}' started"}
    except Exception as e:
        # If something goes wrong, return a 400 error with the error message.
        raise HTTPException(status_code=400, detail=str(e))



# Gracefully shut down a specific VM by name.
# Calls vm_shutdown() from app/services/libvirt_client.py.
@router.post("/{name}/shutdown")
def shutdown_vm(name: str):
    try:
        vm_shutdown(name)
        return {"message": f"VM '{name}' shutdown signaled"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# Force-stop (destroy) a specific VM by name.
# Calls vm_destroy() from app/services/libvirt_client.py.
@router.post("/{name}/destroy")
def destroy_vm(name: str):
    try:
        vm_destroy(name)
        return {"message": f"VM '{name}' force-stopped"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Create a new VM using the provided specification.
# Expects a JSON body matching the CreateVm model (see app/models.py).
# Calls create_vm() from app/services/vm_create.py, which handles disk, cloud-init, and libvirt domain creation.
@router.post("/")
def create_vm_endpoint(spec: CreateVm):
    # 1) Reject duplicate names early
    if get_vm_info(spec.name) is not None:
        raise HTTPException(status_code=409, detail=f"VM '{spec.name}' already exists")

    # 2) Create the VM (non-blocking)
    create_vm(
        name=spec.name,
        vcpus=spec.vcpus,
        memory_mb=spec.memory_mb,
        disk_gb=spec.disk_gb,
        network=spec.network,
        ssh_pubkey=spec.ssh_pubkey,
    )

    # 3) Poll DHCP by MAC (more reliable than hostname)
    macs = get_vm_macs(spec.name)
    ip = _wait_for_ip(macs=macs, network=spec.network, timeout=120, interval=2)

    return {"message": f"VM '{spec.name}' created", "name": spec.name, "ip": ip}

def _wait_for_ip(macs: list[str], network: str = "default", timeout: int = 120, interval: int = 2) -> str | None:
    """
    Poll `virsh net-dhcp-leases <network>` and match leases by MAC addresses.
    Return IPv4 string or None if not found within timeout.
    """
    macs = [m.lower() for m in (macs or [])]
    deadline = time.time() + timeout
    ip_re = re.compile(r"(\d+\.\d+\.\d+\.\d+)/\d+")
    while time.time() < deadline:
        try:
            out = subprocess.check_output(["virsh", "net-dhcp-leases", network], text=True)
            for line in out.splitlines():
                line_l = line.lower()
                if any(mac in line_l for mac in macs):
                    m = ip_re.search(line)
                    if m:
                        return m.group(1)
        except subprocess.CalledProcessError:
            pass
        time.sleep(interval)
    return None

# Delete a VM by name.
# Calls vm_delete() from app/services/libvirt_client.py, which stops, undefines, and removes all storage for the VM.
@router.delete("/{name}")
def delete_vm(name: str):
    try:
        vm_delete(name)
        return {"message": f"VM '{name}' deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Get the IP address of a VM by name using virsh net-dhcp-leases.
# This endpoint parses the output of 'virsh net-dhcp-leases default' to find the IP for the given VM name.
@router.get("/{name}/ip")
def vm_ip(name: str):
    # Import required modules for running shell commands and parsing text
    import subprocess, json, re
    try:
        # Run the virsh command to get DHCP leases for the 'default' network
        out = subprocess.check_output(["virsh", "net-dhcp-leases", "default"], text=True)
        # Loop through each line of the command output
        for line in out.splitlines():
            # Check if the VM name appears in the line
            if name in line:
                # Use a regular expression to find an IPv4 address in the line
                m = re.search(r"(\d+\.\d+\.\d+\.\d+)/\d+", line)
                if m:
                    # If found, return the VM name and its IP address as JSON
                    return {"name": name, "ip": m.group(1)}
        # If no matching line or IP is found, return a 404 error
        raise HTTPException(status_code=404, detail=f"No IP found for {name}")
    except subprocess.CalledProcessError as e:
        # If the virsh command fails, return a 500 error with the error message
        raise HTTPException(status_code=500, detail=e.stderr or str(e))

