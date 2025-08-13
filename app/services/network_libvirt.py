import libvirt  # Import the libvirt library to interact with virtualization hosts
from lxml import etree  # Import lxml.etree for parsing XML
from app.services.libvirt_client import get_conn  # Import a helper to get a libvirt connection

def network_list(uri: str = "qemu:///system") -> list[dict]:
    # List all networks (active and inactive) on the libvirt host
    conn = get_conn(uri)  # Connect to the libvirt daemon
    try:
        out = []
        # Iterate over both active and defined (inactive) networks
        for name in conn.listNetworks() + conn.listDefinedNetworks():
            net = conn.networkLookupByName(name)  # Get the network object by name
            xml = etree.fromstring(net.XMLDesc().encode())  # Parse the network's XML description
            br = xml.findtext(".//bridge[@name]")  # Find the bridge name (if any)
            bridge = xml.find(".//bridge")  # Get the bridge element
            out.append({
                "name": net.name(),  # Network name
                "active": bool(net.isActive()),  # Whether the network is active
                "autostart": bool(net.autostart()),  # Whether the network autostarts with libvirt
                "bridge": bridge.get("name") if bridge is not None else None,  # Bridge name or None
            })
        return out  # Return the list of networks as dictionaries
    finally:
        conn.close()  # Always close the connection

def network_ensure(name: str, bridge: str, uri: str = "qemu:///system"):
    """
    Define/start a libvirt 'bridge' network that binds to an existing Linux bridge.
    Idempotent.
    """
    # Ensure a network with the given name and bridge exists and is running
    conn = get_conn(uri)  # Connect to libvirt
    try:
        try:
            net = conn.networkLookupByName(name)  # Try to find the network by name
        except libvirt.libvirtError:
            net = None  # If not found, set to None

        # XML definition for the network, referencing the existing Linux bridge
        xml = f"""
        <network>
          <name>{name}</name>
          <forward mode='bridge'/>
          <bridge name='{bridge}'/>
        </network>
        """.strip()

        if net is None:
            net = conn.networkDefineXML(xml)  # Define the network if it doesn't exist
        if not net.isActive():
            net.create()  # Start the network if not already active
        net.setAutostart(True)  # Set the network to autostart with libvirt
    finally:
        conn.close()  # Close the connection

def network_delete(name: str, uri: str = "qemu:///system"):
    # Delete a network by name
    conn = get_conn(uri)  # Connect to libvirt
    try:
        net = conn.networkLookupByName(name)  # Find the network by name
        if net.isActive():
            net.destroy()  # Stop the network if it's running
        net.undefine()  # Remove the network definition
    finally:
        conn.close()  # Close the connection

def nic_attach(vm_name: str, network_name: str, uri: str = "qemu:///system"):
    # Attach a network interface (NIC) to a virtual machine
    conn = get_conn(uri)  # Connect to libvirt
    try:
        dom = conn.lookupByName(vm_name)  # Find the VM (domain) by name
        # XML definition for the new network interface (virtio model)
        iface_xml = f"""
        <interface type='network'>
          <source network='{network_name}'/>
          <model type='virtio'/>
        </interface>
        """.strip()
        flags = 0
        try:
            # Set flags to affect both running VM and its config
            flags = getattr(libvirt, "VIR_DOMAIN_AFFECT_LIVE", 0) | getattr(libvirt, "VIR_DOMAIN_AFFECT_CONFIG", 0)
        except Exception:
            flags = 0
        dom.attachDeviceFlags(iface_xml, flags)  # Attach the NIC to the VM
    finally:
        conn.close()  # Close the connection

def nic_detach(vm_name: str, mac_addr: str, uri: str = "qemu:///system"):
    """
    Detach NIC by MAC (lowercase). If unknown, list domain XML first to find it.
    """
    # Detach a network interface from a VM by its MAC address
    conn = get_conn(uri)  # Connect to libvirt
    try:
        dom = conn.lookupByName(vm_name)  # Find the VM by name
        xml = dom.XMLDesc(0)  # Get the VM's XML description
        root = etree.fromstring(xml.encode())  # Parse the XML
        nic = None
        # Look for the interface with the matching MAC address
        for iface in root.findall(".//devices/interface"):
            mac = iface.find("mac")
            if mac is not None and mac.get("address", "").lower() == mac_addr.lower():
                nic = iface
                break
        if nic is None:
            raise RuntimeError(f"MAC {mac_addr} not found on {vm_name}")  # Error if not found
        nic_xml = etree.tostring(nic).decode()  # Convert the interface XML back to string
        flags = getattr(libvirt, "VIR_DOMAIN_AFFECT_LIVE", 0) | getattr(libvirt, "VIR_DOMAIN_AFFECT_CONFIG", 0)
        dom.detachDeviceFlags(nic_xml, flags)  # Detach the NIC from the VM
    finally:
        conn.close()  # Close the connection
