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



@router.get("/{name}/ip")
def vm_ip(name: str, network: str = "default", timeout: int = 5):
    """
    Return the VM's IPv4 address. This function tries two methods:
    1. Use the guest agent (virsh domifaddr) to get the IP from inside the VM.
    2. If that fails, look up the IP in the DHCP leases by matching the VM's MAC address.
    The `timeout` parameter controls how long to wait for each method.
    """
    # Try to get the IP address using the guest agent (domifaddr) first.
    # This method asks the VM directly (if the guest agent is running inside the VM).
    ip = _ip_via_domifaddr(name, timeout=timeout)
    if ip:
        # If we got an IP from the guest agent, return it with the source info.
        return {"name": name, "ip": ip, "source": "guest-agent"}

    # If the guest agent method didn't work, try to get the IP from DHCP leases.
    # First, get the list of MAC addresses for this VM.
    macs = get_vm_macs(name)
    # Now, try to find the IP by looking up the MAC addresses in the DHCP leases.
    ip = _ip_via_dhcp(macs=macs, network=network, timeout=timeout)
    if ip:
        # If we found an IP in the DHCP leases, return it with the source info.
        return {"name": name, "ip": ip, "source": "dhcp-leases"}

    # If neither method worked, return a 404 error saying no IP was found.
    raise HTTPException(status_code=404, detail=f"No IP found for {name}")
# Helper function to get IP via guest agent (domifaddr).
def _ip_via_domifaddr(name: str, timeout: int = 5) -> str | None:
    """
    Try to get the VM's IP address using the guest agent (virsh domifaddr).
    This function will keep trying for up to `timeout` seconds.
    Returns the IP address as a string if found, or None if not found.
    """
    deadline = time.time() + timeout  # Calculate the time when we should stop trying.
    ip_re = re.compile(r"(\d+\.\d+\.\d+\.\d+)/\d+")  # Regex to match IPv4 addresses like 192.168.1.10/24
    while time.time() < deadline:
        try:
            # Run the command: virsh domifaddr <name> to get the VM's network info from the guest agent.
            out = subprocess.check_output(["virsh", "domifaddr", name], text=True)
            # Search the output for an IPv4 address using the regex.
            m = ip_re.search(out)
            if m:
                # If we found an IP address, return just the IP part (not the /24 subnet).
                return m.group(1)
        except subprocess.CalledProcessError:
            # If the command fails (e.g., guest agent not running), just ignore and try again.
            pass
        # Wait 1 second before trying again (so we don't spam the system).
        time.sleep(1)
    # If we never found an IP, return None.
    return None

def _ip_via_dhcp(macs: list[str], network: str = "default", timeout: int = 5) -> str | None:
    """
    Poll virsh net-dhcp-leases and match leases by MAC addresses.
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
        time.sleep(1)
    return None


