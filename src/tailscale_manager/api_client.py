import re

import httpx

BASE_URL = "https://api.tailscale.com/api/v2"


def _strip_hujson(text: str) -> str:
    text = re.sub(r"(?ms)//.*?$|/\*.*?\*/", "", text)
    result = []
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
        elif ch == "\\" and in_string:
            escape = True
        elif ch == '"' and not escape:
            in_string = not in_string
        if not in_string and ch == "#":
            continue
        result.append(ch)
    cleaned = "".join(result)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


class TailscaleAPIError(Exception):
    pass


class TailscaleAPIClient:
    def __init__(self, api_key: str, tailnet: str = ""):
        self._auth = (api_key, "")
        self._tailnet = tailnet
        self._headers = {"Accept": "application/json"}

    def _url(self, path: str) -> str:
        return f"{BASE_URL}/tailnet/{self._tailnet}{path}" if self._tailnet else f"{BASE_URL}{path}"

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = self._url(path)
        headers = {**self._headers, **kwargs.pop("headers", {})}
        resp = httpx.request(method, url, auth=self._auth, headers=headers, **kwargs, timeout=30)
        if resp.status_code >= 400:
            detail = resp.text[:300]
            raise TailscaleAPIError(f"HTTP {resp.status_code}: {detail}")
        if not resp.content:
            return {}
        try:
            return resp.json()
        except Exception:
            cleaned = _strip_hujson(resp.text)
            return httpx.Response(200, text=cleaned).json()

    @property
    def authenticated(self) -> bool:
        return bool(self._auth[0])

    def whoami(self) -> dict:
        return self._request("GET", "/api/v2/whoami")

    def get_acl(self) -> dict:
        return self._request("GET", "/acl")

    def set_acl(self, acl: dict, etag: str = "") -> dict:
        headers = {"Content-Type": "application/json"}
        if etag:
            headers["If-Match"] = etag
        return self._request("POST", "/acl", json=acl, headers=headers)

    def validate_acl(self, acl: dict) -> list:
        try:
            resp = self._request("POST", "/acl/validate", json=acl)
            return resp.get("warnings", [])
        except TailscaleAPIError as e:
            raise e

    def list_devices(self) -> list[dict]:
        data = self._request("GET", "/devices")
        return data.get("devices", [])

    def get_device(self, device_id: str) -> dict:
        return self._request("GET", f"/devices/{device_id}")

    def get_contacts(self) -> dict:
        data = self._request("GET", "/contacts")
        return data.get("contacts", [])

    def list_dns_nameservers(self) -> list:
        data = self._request("GET", "/dns/nameservers")
        return data.get("dns", [])

    def get_keys(self) -> list[dict]:
        data = self._request("GET", "/keys")
        return data.get("keys", [])
