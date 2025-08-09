
# Import standard Python modules for file and process management
import os, subprocess, tempfile, textwrap, uuid, pathlib
# Import Optional for type hinting (allows a value to be None)
from typing import Optional

# Path to the base Ubuntu cloud image used for new VMs
BASE_IMG = "/var/lib/libvirt/images/base/jammy-server-cloudimg-amd64.img"
# Directory where VM disk images and seed ISOs will be stored
IMAGES_DIR = "/var/lib/libvirt/images"


# Helper function to run a shell command and raise an error if it fails
def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


# Create a cloud-init seed ISO for the VM, containing user-data and meta-data
# This ISO is used to set the hostname, user, and SSH key on first boot
# (Referenced in create_vm below)
def _mk_seed_iso(name: str, username: str, ssh_pubkey: Optional[str]) -> str:
    user_data = [
        "#cloud-config",
        f"hostname: {name}",
        # Create a user with sudo privileges and no password required
        f"users:\n  - name: {username}\n    groups: [sudo]\n    shell: /bin/bash\n    sudo: ['ALL=(ALL) NOPASSWD:ALL']",
    ]
    if ssh_pubkey:
        # If an SSH public key is provided, add it to the authorized_keys
        user_data.append(f"    ssh_authorized_keys:\n      - {ssh_pubkey}")

    # meta-data for cloud-init (instance ID and hostname)
    meta_data = f"instance-id: {uuid.uuid4()}\nlocal-hostname: {name}\n"

    # Create a temporary directory to hold the files
    with tempfile.TemporaryDirectory() as td:
        ud = pathlib.Path(td, "user-data"); md = pathlib.Path(td, "meta-data")
        # Write user-data and meta-data files
        ud.write_text("\n".join(user_data) + "\n", encoding="utf-8")
        md.write_text(meta_data, encoding="utf-8")
        # Create the seed ISO using cloud-localds
        iso = pathlib.Path(td, f"{name}-seed.iso")
        _run(["cloud-localds", str(iso), str(ud), str(md)])
        # Move the ISO to the images directory (requires sudo)
        final = os.path.join(IMAGES_DIR, f"{name}-seed.iso")
        _run(["sudo", "mv", str(iso), final])
    # Return the path to the final ISO
    return final


# Create a new VM with the given parameters
# This function is called by the create_vm_endpoint in app/routers/vms.py
# Parameters are validated by the CreateVm model in app/models.py
def create_vm(*, name: str, vcpus: int, memory_mb: int, disk_gb: int, network: str, ssh_pubkey: Optional[str]):
    # Path for the new VM's disk image
    disk_path = os.path.join(IMAGES_DIR, f"{name}.qcow2")
    # Create a new disk image as a copy-on-write overlay of the base image
    _run(["sudo", "qemu-img", "create", "-f", "qcow2", "-F", "qcow2", "-b", BASE_IMG, disk_path, f"{disk_gb}G"])
    # Create a cloud-init seed ISO for the VM
    seed_iso = _mk_seed_iso(name, username="ubuntu", ssh_pubkey=ssh_pubkey)

    # Use virt-install to define and start the VM
    # --import: use the existing disk image (no OS installer)
    # --os-variant: helps virt-install optimize for Ubuntu 22.04
    # --network: attach to the specified libvirt network
    # --graphics none: no graphical console (headless)
    # --noautoconsole: don't automatically open a console
    # --wait -1: wait until install is complete
    _run([
        "sudo", "virt-install",
        "--name", name,
        "--memory", str(memory_mb),
        "--vcpus", str(vcpus),
        "--disk", f"path={disk_path},format=qcow2,cache=none",
        "--disk", f"path={seed_iso},device=cdrom",
        "--import",  # use existing disk (cloud image) without an installer
        "--os-variant", "ubuntu22.04",
        "--network", f"network={network}",
        "--graphics", "none",
        "--noautoconsole",
        "--wait", "-1"
    ])
