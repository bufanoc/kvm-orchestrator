# CLI Usage — `kvm-orchestrator`

A thin, friendly wrapper over the FastAPI backend. Works against your local server (`http://127.0.0.1:8000` by default) or any base URL you set.

> Tip: Activate your venv first so the `kvm-orchestrator` command is on PATH.
>
> ```bash
> source .venv/bin/activate
> ```

---

## Setup

### Set API base URL
```bash
kvm-orchestrator set-url http://127.0.0.1:8000
# This stores the URL in ~/.kvm_orchestrator/config.json.
# You can also override with KVM_ORCH_URL environment variable.


# VM lifecycle (available now)
kvm-orchestrator list


# Create a VM
kvm-orchestrator create \
  --name demo-01 \
  --vcpu 2 \
  --ram 2048 \
  --disk 10 \
  --network default \
  --ssh-pubkey @"$HOME/.ssh/id_rsa.pub"
# Returns a message and the VM’s IP (once DHCP assigns it).
# If ip is null, use kvm-orchestrator ip <name> after a few seconds.


# Get VM ip
kvm-orchestrator ip demo-01
# Uses guest agent (virsh domifaddr) first; falls back to DHCP leases by MAC.


# Start / Shutdown / Destroy / Delete
kvm-orchestrator start demo-01     # power on
kvm-orchestrator shutdown demo-01  # graceful ACPI shutdown
kvm-orchestrator destroy demo-01   # hard stop (power cut)
kvm-orchestrator delete demo-01    # undefine and remove storage/NVRAM

#-----------------------------------------------------------------------------------
# Server control (Makefile helpers)

# Run the API in foreground (dev logs in terminal)
make run

# Run in background with logs uvicorn.log, PID-> .uvicorn.pid
make up 
make logs
make down

# Power tips
# Use a different API without changing the saved URL
KVM_ORCH_URL=http://kvm-host:8000 kvm-orchestrator list

# Shell completion (Typer)
kvm-orchestrator --install-completion
# restart your shell

#------------------ Roadmap (planned CLI commands)-------------------------------
# These will arrive as the backend grows—syntax reserved now so we keep a stable UX.
# Hosts (multi-host control)

kvm-orchestrator host list
kvm-orchestrator host add my-lab --url http://kvm-dev:8000
kvm-orchestrator host remove my-lab

# Images (manage base images)
kvm-orchestrator image list
kvm-orchestrator image add ubuntu-jammy --url https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img
kvm-orchestrator image remove ubuntu-jammy

# Networks (prep for Arista integration)
kvm-orchestrator network list
kvm-orchestrator network create br-vlan10 --bridge br0 --vlan 10
kvm-orchestrator network delete br-vlan10
kvm-orchestrator vm nic-attach demo-01 --network br-vlan10
kvm-orchestrator vm nic-detach demo-01 --network br-vlan10

# VM templates (quality-of-life)
kvm-orchestrator template list
kvm-orchestrator template add small --vcpu 2 --ram 2048 --disk 20
kvm-orchestrator vm create --name web-01 --template small --image ubuntu-jammy --network default --ssh-pubkey @~/.ssh/id_rsa.pub

# Troubleshooting
# “command not found: kvm-orchestrator”
# Ensure your venv is active and the wrapper exists:
source .venv/bin/activate
which kvm-orchestrator

# If missing, (re)create the wrapper and link:
#---block-start----------------------------------
mkdir -p tools
cat > tools/kvm-orchestrator <<'SH'
#!/usr/bin/env bash
set -e
if [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
  PY="$VIRTUAL_ENV/bin/python"
elif [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi
exec "$PY" -m cli "$@"
SH
chmod +x tools/kvm-orchestrator
ln -sf "$(pwd)/tools/kvm-orchestrator" .venv/bin/kvm-orchestrator
#--------block-end--------------------------------

# Create returns ip: null
# Give it ~10–30s on first boot. Then:
kvm-orchestrator ip <vm-name>

# Delete fails with nvram flag errors
# You are likely on older libvirt; our API now detects flags and manually removes leftovers.

---


