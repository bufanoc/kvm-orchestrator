
# Import BaseModel and Field from Pydantic. Pydantic is used for data validation and settings management using Python type annotations.
from pydantic import BaseModel, Field
# Import Optional from typing, which allows a field to be None (not required).
from typing import Optional

# Define a data model for creating a new VM. This model is used to validate and document the expected input for VM creation endpoints.
# (Referenced in app/routers/vms.py and app/services/vm_create.py)
class CreateVm(BaseModel):
    # The name of the VM. Must be 1-32 characters, letters, numbers, or dashes only.
    name: str = Field(pattern=r"^[a-zA-Z0-9-]{1,32}$")
    # Number of virtual CPUs for the VM. Default is 2.
    vcpus: int = 2
    # Amount of memory (in megabytes) for the VM. Default is 2048 MB (2 GB).
    memory_mb: int = 2048
    # Size of the VM's disk (in gigabytes). Default is 10 GB.
    disk_gb: int = 10
    # Name of the libvirt network to attach the VM to. Default is 'default'.
    network: str = "default"          # libvirt network name
    # SSH public key to inject into the VM for remote access. Optional; if not provided, no key is injected.
    ssh_pubkey: Optional[str] = None  # user’s ~/.ssh/id_rsa.pub
