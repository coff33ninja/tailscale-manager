import os
import pytest
from dotenv import load_dotenv

load_dotenv()


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "write_op: marks tests that modify state (use with caution)",
    )


@pytest.fixture(scope="session")
def api_key() -> str:
    key = os.environ.get("TAILSCALE_API_KEY", "")
    if not key:
        pytest.skip("TAILSCALE_API_KEY not set")
    if not key.startswith("tskey-"):
        pytest.skip("TAILSCALE_API_KEY must start with tskey-")
    return key


@pytest.fixture(scope="session")
def tailnet() -> str:
    tn = os.environ.get("TAILSCALE_TAILNET", "")
    if not tn:
        pytest.skip("TAILSCALE_TAILNET not set")
    return tn
