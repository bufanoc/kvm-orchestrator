import sys
from typing import Optional

import typer
from .client import api, save_base_url

app = typer.Typer(help="KVM Orchestrator CLI")

# ----- config -----
@app.command("set-url")
def set_url(url: str = typer.Argument(..., help="Base API URL, e.g. http://127.0.0.1:8000")):
    """Persist the API base URL (~/.kvm_orchestrator/config.json)."""
    save_base_url(url)
    typer.echo(f"Saved base_url = {url}")

# ----- VM list -----
@app.command("list")
def list_vms():
    """List VMs."""
    base, s = api()
    r = s.get(f"{base}/vms/")
    r.raise_for_status()
    vms = r.json().get("vms", [])
    if not vms:
        typer.echo("No VMs found.")
        raise typer.Exit(0)
    # simple table
    typer.echo(f"{'NAME':20} {'STATE':10} ACTIVE")
    for vm in vms:
        typer.echo(f"{vm['name']:20} {vm['state']:10} {str(vm['active']).lower()}")

# ----- VM IP -----
@app.command("ip")
def vm_ip(name: str = typer.Argument(..., help="VM name")):
    """Get a VM's IP (guest-agent with DHCP fallback)."""
    base, s = api()
    r = s.get(f"{base}/vms/{name}/ip")
    if r.status_code == 404:
        typer.echo("No IP found.")
        raise typer.Exit(1)
    r.raise_for_status()
    data = r.json()
    typer.echo(f"{name}: {data['ip']} ({data.get('source','?')})")

# ----- VM start/stop/destroy/delete -----
@app.command("start")
def start_vm(name: str):
    base, s = api()
    r = s.post(f"{base}/vms/{name}/start")
    r.raise_for_status()
    typer.echo(r.json()["message"])

@app.command("shutdown")
def shutdown_vm(name: str):
    base, s = api()
    r = s.post(f"{base}/vms/{name}/shutdown")
    r.raise_for_status()
    typer.echo(r.json()["message"])

@app.command("destroy")
def destroy_vm(name: str):
    base, s = api()
    r = s.post(f"{base}/vms/{name}/destroy")
    r.raise_for_status()
    typer.echo(r.json()["message"])

@app.command("delete")
def delete_vm(name: str):
    base, s = api()
    r = s.delete(f"{base}/vms/{name}")
    r.raise_for_status()
    typer.echo(r.json()["message"])

# ----- VM create -----
@app.command("create")
def create_vm(
    name: str = typer.Option(..., "--name", "-n", help="VM name"),
    vcpu: int = typer.Option(2, "--vcpu", help="vCPU count"),
    ram: int = typer.Option(2048, "--ram", help="Memory (MB)"),
    disk: int = typer.Option(10, "--disk", help="Disk (GB)"),
    network: str = typer.Option("default", "--network", help="Libvirt network"),
    ssh_pubkey: Optional[str] = typer.Option(None, "--ssh-pubkey",
        help="Public key string or @/path/to/key.pub"),
):
    """Create a VM and print its IP when ready (API returns as soon as domain starts)."""
    base, s = api()

    key = None
    if ssh_pubkey:
        key = ssh_pubkey
        if ssh_pubkey.startswith("@"):
            from pathlib import Path
            key = Path(ssh_pubkey[1:]).read_text().strip()

    payload = {
        "name": name,
        "vcpus": vcpu,
        "memory_mb": ram,
        "disk_gb": disk,
        "network": network,
        "ssh_pubkey": key,
    }

    r = s.post(f"{base}/vms/", json=payload)
    if r.status_code == 409:
        typer.secho(r.json().get("detail", "duplicate name"), fg=typer.colors.RED)
        raise typer.Exit(1)
    r.raise_for_status()
    data = r.json()
    typer.echo(data["message"])
    typer.echo(f"IP: {data.get('ip')}")

def main():
    app()

if __name__ == "__main__":
    sys.exit(main())
