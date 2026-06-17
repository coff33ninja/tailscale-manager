import os
from pathlib import Path

from dotenv import load_dotenv, set_key, unset_key

CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "tailscale-manager"
CONFIG_ENV = CONFIG_DIR / ".env"
PROJECT_ENV = Path(__file__).resolve().parent.parent.parent / ".env"


def load() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    load_dotenv(CONFIG_ENV, override=False)
    load_dotenv(PROJECT_ENV, override=False)
    return {
        "api_key": os.environ.get("TAILSCALE_API_KEY", ""),
        "tailnet": os.environ.get("TAILSCALE_TAILNET", ""),
    }


def save(api_key: str, tailnet: str = "") -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    env_path = str(CONFIG_ENV)
    if api_key:
        set_key(env_path, "TAILSCALE_API_KEY", api_key)
    else:
        unset_key(env_path, "TAILSCALE_API_KEY")
    if tailnet:
        set_key(env_path, "TAILSCALE_TAILNET", tailnet)
    else:
        unset_key(env_path, "TAILSCALE_TAILNET")

