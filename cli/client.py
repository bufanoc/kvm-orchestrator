import os, json, requests
from pathlib import Path

DEFAULT_URL = "http://127.0.0.1:8000"
CONF_PATH = Path.home() / ".kvm_orchestrator" / "config.json"

def load_config() -> dict:
    if CONF_PATH.exists():
        try:
            return json.loads(CONF_PATH.read_text())
        except Exception:
            pass
    return {"base_url": os.environ.get("KVM_ORCH_URL", DEFAULT_URL)}

def api():
    cfg = load_config()
    base = cfg.get("base_url", DEFAULT_URL).rstrip("/")
    session = requests.Session()
    # future: session.headers.update({"Authorization": f"Bearer {cfg['token']}"})
    return base, session

def save_base_url(url: str) -> None:
    CONF_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONF_PATH.write_text(json.dumps({"base_url": url}, indent=2))
