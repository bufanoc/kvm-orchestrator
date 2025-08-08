# Apprenticeship Project Log

**Project:** KVM Orchestrator with Arista VLAN Integration  
**Apprentice:** Carmine  
**Mentor:** ChatGPT (GPT-5)  
**Start Date:** 2025-08-07  

---

## 📅 Week 1 — Setup & Foundation
**Goals:**
- Set up dev environment (Ubuntu VM, VS Code, GitHub)
- Establish Git workflow (local + remote repo)
- Scaffold a minimal FastAPI app with health endpoint
- Begin integration with KVM via libvirt (read-only)

**Tasks Completed:**
- [x] Created GitHub repo: `kvm-orchestrator`
- [x] Connected local repo to GitHub remote
- [x] Added `.gitignore` for Python
- [x] Renamed branch from `master` to `main`
- [x] Scaffolded FastAPI app with `/` and `/status` endpoints
- [x] Added `docs/apprenticeship-log.md` for progress tracking
- [x] Installed and configured KVM + libvirt on Ubuntu 22.04 Server
- [ ] Implemented `/vms` endpoint to list all defined and running VMs via libvirt

**In Progress:**
- Expanding libvirt integration to include VM creation, shutdown, and deletion

**Blocked:**
- None

**Notes / Lessons Learned:**
- Verified nested virtualization in vSphere (`egrep -c '(vmx|svm)' /proc/cpuinfo`)
- Installed `libvirt-dev` before `pip install libvirt-python` to avoid build errors
- Using `qemu:///system` URI for local libvirt connections
- `virsh list --all` is a quick way to confirm libvirt state matches API output

**Next Steps:**
- Implement API endpoint for creating a new VM via cloud-init
- Add start/stop/delete VM endpoints
- Begin planning network integration for Arista VLANs
