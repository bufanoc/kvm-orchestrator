
# Import the libvirt Python bindings, which allow us to control and query virtual machines managed by libvirt (like KVM/QEMU)
import os
import libvirt
from lxml import etree  # ensure lxml is in requirements
# This dictionary maps numeric VM states (as returned by libvirt) to human-readable strings
STATE_MAP = {
    0: "nostate", 1: "running", 2: "blocked", 3: "paused",
    4: "shutdown", 5: "shutoff", 6: "crashed", 7: "pmsuspended",
}


# Open a connection to the libvirt daemon (default: system-wide QEMU/KVM)
# Returns a connection object, or raises an error if it fails
def get_conn(uri: str = "qemu:///system"):
    conn = libvirt.open(uri)
    if conn is None:
        # If connection fails, raise an error
        raise RuntimeError(f"Failed to open libvirt connection to {uri}")
    return conn


# List all virtual machines (both running and defined-but-stopped)
# Returns a list of summary dictionaries for each VM
def list_vms(uri: str = "qemu:///system"):
    conn = get_conn(uri)
    try:
        items = []
        # Loop through all running VMs by their IDs
        for id_ in conn.listDomainsID():        # running
            dom = conn.lookupByID(id_)
            items.append(_domain_summary(dom))
        # Loop through all defined but not running VMs by their names
        for name in conn.listDefinedDomains():  # defined but stopped
            dom = conn.lookupByName(name)
            items.append(_domain_summary(dom))
        return items
    finally:
        # Always close the connection to free resources
        conn.close()


# Get detailed information about a specific VM by name
# Returns a dictionary of VM details, or None if not found
def get_vm_info(name: str, uri: str = "qemu:///system"):
    conn = get_conn(uri)
    try:
        try:
            # Try to look up the VM by name
            dom = conn.lookupByName(name)
        except libvirt.libvirtError:
            # If not found, return None
            return None
        # Return detailed info about the VM
        return _domain_details(dom)
    finally:
        conn.close()


# Start a VM by name (if it is not already running)

# Start a VM by name (if it is not already running)
def vm_start(name: str, uri: str = "qemu:///system"):
    conn = get_conn(uri)
    try:
        dom = conn.lookupByName(name)
        if dom.isActive() != 1:
            dom.create()
    finally:
        conn.close()


# Gracefully shut down a VM by name (sends ACPI shutdown signal)

# Gracefully shut down a VM by name (sends ACPI shutdown signal)
def vm_shutdown(name: str, uri: str = "qemu:///system"):
    conn = get_conn(uri)
    try:
        dom = conn.lookupByName(name)
        dom.shutdown()  # graceful ACPI
    finally:
        conn.close()


# Force-stop (destroy) a VM by name (immediate power off)

# Force-stop (destroy) a VM by name (immediate power off)
def vm_destroy(name: str, uri: str = "qemu:///system"):
    conn = get_conn(uri)
    try:
        dom = conn.lookupByName(name)
        dom.destroy()  # hard stop
    finally:
        conn.close()


# Helper function: summarize a VM's basic info (name, uuid, state, active)
def _domain_summary(dom):
    state, _ = dom.state()
    return {
        "name": dom.name(),
        "uuid": dom.UUIDString(),
        "state": STATE_MAP.get(state, str(state)),
        "active": bool(dom.isActive()),
    }


# Helper function: get detailed info about a VM (adds vcpus and memory info)
def _domain_details(dom):
    info = _domain_summary(dom)
    try:
        # dom.info() returns: (state, maxMemKiB, memoryKiB, nrVirtCpu, cpuTime)
        st, maxMem, memCur, vcpus, _cpuTime = dom.info()
        info.update({
            "vcpus": vcpus,
            "memory_kib_max": maxMem,
            "memory_kib_cur": memCur,
        })
    except Exception:
        # If we can't get details, just skip them
        pass
    return info


def vm_start(name: str, uri: str = "qemu:///system"):
    conn = get_conn(uri)
    try:
        dom = conn.lookupByName(name)
        if dom.isActive() != 1:
            dom.create()
    finally:
        conn.close()

def vm_shutdown(name: str, uri: str = "qemu:///system"):
    conn = get_conn(uri)
    try:
        dom = conn.lookupByName(name)
        dom.shutdown()  # graceful ACPI
    finally:
        conn.close()

def vm_destroy(name: str, uri: str = "qemu:///system"):
    conn = get_conn(uri)
    try:
        dom = conn.lookupByName(name)
        dom.destroy()  # hard stop
    finally:
        conn.close()


# newest
def vm_delete(name: str, uri: str = "qemu:///system"):
    """
    Stop if running, undefine domain, and remove storage/NVRAM.
    Works even when older libvirt-python is missing some flags.
    """
    conn = get_conn(uri)
    try:
        dom = conn.lookupByName(name)

        # Collect file paths BEFORE undefine (so we can remove leftovers)
        xml = dom.XMLDesc(0)
        root = etree.fromstring(xml.encode())

        # All <disk><source file="..."> paths (qcow2, seed ISO, etc.)
        disk_paths = []
        for src in root.findall(".//devices/disk/source"):
            p = src.get("file") or src.get("dev") or src.get("name")
            if p:
                disk_paths.append(p)

        nvram_path = root.findtext(".//os/nvram")

        # Stop if running
        if dom.isActive() == 1:
            dom.destroy()

        # Build flags with feature detection
        flags = 0
        flags |= getattr(libvirt, "VIR_DOMAIN_UNDEFINE_MANAGED_SAVE", 0)
        flags |= getattr(libvirt, "VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA", 0)
        if nvram_path:
            flags |= getattr(libvirt, "VIR_DOMAIN_UNDEFINE_NVRAM", 0)
        # On newer libvirt, this removes storage; on older, it's just 0
        flags |= getattr(libvirt, "VIR_DOMAIN_UNDEFINE_REMOVE_ALL_STORAGE", 0)

        try:
            dom.undefineFlags(flags)
        except libvirt.libvirtError:
            # Fallback for old bindings with minimal flag support
            dom.undefine()

        # Manual cleanup in case REMOVE_ALL_STORAGE wasn't supported
        for p in set(filter(None, disk_paths + ([nvram_path] if nvram_path else []))):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

    finally:
        conn.close()
