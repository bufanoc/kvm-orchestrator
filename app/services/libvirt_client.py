import libvirt

STATE_MAP = {
    0: "nostate", 1: "running", 2: "blocked", 3: "paused",
    4: "shutdown", 5: "shutoff", 6: "crashed", 7: "pmsuspended",
}

def get_conn(uri: str = "qemu:///system"):
    conn = libvirt.open(uri)
    if conn is None:
        raise RuntimeError(f"Failed to open libvirt connection to {uri}")
    return conn

def list_vms(uri: str = "qemu:///system"):
    conn = get_conn(uri)
    try:
        items = []
        for id_ in conn.listDomainsID():        # running
            dom = conn.lookupByID(id_)
            items.append(_domain_summary(dom))
        for name in conn.listDefinedDomains():  # defined but stopped
            dom = conn.lookupByName(name)
            items.append(_domain_summary(dom))
        return items
    finally:
        conn.close()

def get_vm_info(name: str, uri: str = "qemu:///system"):
    conn = get_conn(uri)
    try:
        try:
            dom = conn.lookupByName(name)
        except libvirt.libvirtError:
            return None
        return _domain_details(dom)
    finally:
        conn.close()

def vm_start(name: str, uri: str = "qemu:///system"):
    conn = get_conn(uri)
    try:
        dom = conn.lookupByName(name)
        if dom.isActive() == 1:
            return
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

def _domain_summary(dom):
    state, _ = dom.state()
    return {
        "name": dom.name(),
        "uuid": dom.UUIDString(),
        "state": STATE_MAP.get(state, str(state)),
        "active": bool(dom.isActive()),
    }

def _domain_details(dom):
    info = _domain_summary(dom)
    try:
        vcpus, maxmem, mem, _t1, _t2 = None, None, None, None, None
        # dom.info(): (state, maxMemKiB, memoryKiB, nrVirtCpu, cpuTime)
        st, maxMem, memCur, vcpus, _cpuTime = dom.info()
        info.update({
            "vcpus": vcpus,
            "memory_kib_max": maxMem,
            "memory_kib_cur": memCur,
        })
    except Exception:
        pass
    return info
