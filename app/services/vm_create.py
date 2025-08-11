
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
# This ISO is used to set up the VM's hostname, user account, SSH key, and install the qemu-guest-agent on first boot.
# (Referenced in create_vm below)
def _mk_seed_iso(name: str, username: str, ssh_pubkey: Optional[str]) -> str:
    # Build the cloud-init user-data file as a list of lines (YAML format)
    lines = [
        "#cloud-config",  # Tells cloud-init this is a config file
        f"hostname: {name}",  # Set the VM's hostname
        "package_update: true",  # Update package list on first boot
        "packages:",
        "  - qemu-guest-agent",  # Install the qemu-guest-agent package
        "users:",
        f"  - name: {username}",  # Create a user with the given username
        "    groups: [sudo]",  # Add user to sudo group
        "    shell: /bin/bash",  # Set default shell
        "    sudo: ['ALL=(ALL) NOPASSWD:ALL']",  # Allow passwordless sudo
    ]
    # If an SSH public key is provided, add it to the user's authorized_keys
    if ssh_pubkey:
        lines += [
            "    ssh_authorized_keys:",
            f"      - {ssh_pubkey}",
        ]

    # Add a command to enable and start the qemu-guest-agent service on boot
    lines += [
        "runcmd:",
        "  - [ systemctl, enable, --now, qemu-guest-agent ]",
    ]

    # Join all lines into a single string for the user-data file
    user_data = "\n".join(lines) + "\n"
    # Create meta-data file with a unique instance ID and the hostname
    meta_data = f"instance-id: {uuid.uuid4()}\nlocal-hostname: {name}\n"

    # Create a temporary directory to hold the files before making the ISO
    with tempfile.TemporaryDirectory() as td:
        ud = pathlib.Path(td, "user-data")  # Path for user-data file
        md = pathlib.Path(td, "meta-data")  # Path for meta-data file
        ud.write_text(user_data, encoding="utf-8")  # Write user-data
        md.write_text(meta_data, encoding="utf-8")  # Write meta-data
        iso = pathlib.Path(td, f"{name}-seed.iso")  # Path for the ISO file
        # Use cloud-localds to create the seed ISO from user-data and meta-data
        _run(["cloud-localds", str(iso), str(ud), str(md)])
        final = os.path.join(IMAGES_DIR, f"{name}-seed.iso")  # Final destination
        # Move the ISO to the images directory (requires sudo)
        _run(["sudo", "mv", str(iso), final])
    # Return the path to the final ISO file
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
        "--wait", "0" # <-- was "-1"; 0 = return immediately after start
    ])
