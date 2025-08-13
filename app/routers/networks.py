from fastapi import APIRouter, HTTPException  # Import FastAPI tools for routing and error handling
from app.models import NetworkCreate  # Import the model for network creation requests
from app.services.network_libvirt import network_list, network_ensure, network_delete, nic_attach, nic_detach  # Import network functions

router = APIRouter(prefix="/networks", tags=["networks"])  # Create a router for network-related endpoints

@router.get("/")
def list_networks():
    # Endpoint to list all networks
    return {"networks": network_list()}

@router.post("/")
def create_network(spec: NetworkCreate):
    # Endpoint to create a new network using the provided specification
    try:
        network_ensure(spec.name, spec.bridge)  # Ensure the network exists and is started
        return {"message": f"network '{spec.name}' bound to bridge '{spec.bridge}'"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))  # Return error if something goes wrong

@router.delete("/{name}")
def delete_network(name: str):
    # Endpoint to delete a network by its name
    try:
        network_delete(name)  # Delete the specified network
        return {"message": f"network '{name}' deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))  # Return error if something goes wrong

@router.post("/attach")
def attach(vm: str, network: str):
    # Endpoint to attach a VM to a network
    try:
        nic_attach(vm, network)  # Attach the network interface to the VM
        return {"message": f"attached {vm} to {network}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))  # Return error if something goes wrong

@router.post("/detach")
def detach(vm: str, mac: str):
    # Endpoint to detach a network interface from a VM using its MAC address
    try:
        nic_detach(vm, mac)  # Detach the network interface from the VM
        return {"message": f"detached {mac} from {vm}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))  # Return error if something goes wrong
