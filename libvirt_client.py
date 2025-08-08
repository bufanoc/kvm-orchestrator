
# libvirt_client.py
# This module provides functions to interact with the libvirt virtualization system (KVM/QEMU)
import libvirt

# Map numeric VM states from libvirt to human-readable strings
STATE_MAP = {
    0: "nostate",
    1: "running",
    2: "blocked",
    3: "paused",
    4: "shutdown",
    5: "shutoff",
    6: "crashed",
    7: "pmsuspended",
}


# Opens a read/write connection to the system libvirt instance
def get_conn(uri: str = "qemu:///system"):
    conn = libvirt.open(uri)
    if conn is None:
        # If connection fails, raise an error
        raise RuntimeError(f"Failed to open libvirt connection to {uri}")
    return conn


# Returns a list of all virtual machines (running and defined but not running)
# Each VM is represented as a dictionary with name, uuid, and state
def list_vms(uri: str = "qemu:///system"):
    conn = get_conn(uri)
    try:
        domains = []
        # Get all running VMs by their IDs
        for id_ in conn.listDomainsID():
            dom = conn.lookupByID(id_)
            state, _ = dom.state()
            # Add VM info to the list
            domains.append({
                "name": dom.name(),
                "uuid": dom.UUIDString(),
                "state": STATE_MAP.get(state, str(state))
            })
        # Get all defined but not running VMs by their names
        for name in conn.listDefinedDomains():
            dom = conn.lookupByName(name)
            state, _ = dom.state()
            domains.append({
                "name": dom.name(),
                "uuid": dom.UUIDString(),
                "state": STATE_MAP.get(state, str(state))
            })
        return domains
    finally:
        # Always close the connection to free resources
        conn.close()
