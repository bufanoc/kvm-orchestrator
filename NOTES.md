# Project Notes — KVM Orchestrator

This file is a scratchpad for quick notes, commands, troubleshooting steps, and ideas.  
Not meant to be clean — just dump info here as you work.

---

## 🗓️ August/07/2025 — What I Worked On
- Tested FastAPI `/status` endpoint from browser
- Confirmed GitHub push from VM


---

## 💻 Commands Used
```bash
# Usefull Commands
# Activate the Python virtual environment
source .venv/bin/activate

# Start FastAPI server accessible from any IP on port 8000 (for remote access)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start FastAPI server on localhost only (for local development)
uvicorn main:app --reload

# Generate requirements.txt file with all installed packages and versions
pip freeze > requirements.txt

# Check current Git status (see what files are modified/staged)
git status

# Check remote repository URLs
git remote -v

# Stage specific files for commit
git add main.py requirements.txt

# Stage documentation file for commit
git add docs/apprenticeship-log.md

# Create a commit with a descriptive message
git commit -m "Scaffold FastAPI app with health endpoint"

# Push committed changes to remote repository (GitHub)
git push


# Useful Commands

# Use to ssh into a new vm change the username and ip to your use
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@192.168.122.xx
