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

    def _request(self, method: str, path: str, tailnet_scope: bool = True, **kwargs) -> dict | list:
        if path.startswith("/api/v2/"):
            path = path[len("/api/v2"):]
        if tailnet_scope and self._tailnet:
            url = f"{BASE_URL}/tailnet/{self._tailnet}{path}"
        else:
            url = f"{BASE_URL}{path}"
        headers = {**self._headers, **kwargs.pop("headers", {})}
        resp = httpx.request(method, url, auth=self._auth, headers=headers, **kwargs, timeout=30)
        if resp.status_code >= 400:
            detail = resp.text[:300]
            raise TailscaleAPIError(f"HTTP {resp.status_code}: {detail}")
        if not resp.content:
            return {}
        try:
            data = resp.json()
            return data if data is not None else {}
        except Exception:
            cleaned = _strip_hujson(resp.text)
            return httpx.Response(200, text=cleaned).json()

    def reconfigure(self, api_key: str, tailnet: str = ""):
        self._auth = (api_key, "")
        self._tailnet = tailnet

    @property
    def authenticated(self) -> bool:
        return bool(self._auth[0])

    # ── Whoami ──
    def whoami(self) -> dict:
        return self._request("GET", "/whoami", tailnet_scope=False)

    # ── ACL / Policy ──
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

    def preview_acl(self, acl: dict, type: str = "user", preview_for: str = "") -> list:
        if not preview_for:
            users = self.list_users()
            if users:
                preview_for = users[0].get("loginName", "")
            else:
                preview_for = "*"
        params = {"type": type, "previewFor": preview_for}
        resp = self._request("POST", "/acl/preview", params=params, json=acl)
        return resp.get("matches", [])

    # ── Devices ──
    def list_devices(self, **filters) -> list[dict]:
        data = self._request("GET", "/devices", params=filters or None)
        return data.get("devices", [])

    def get_device(self, device_id: str) -> dict:
        return self._request("GET", f"/device/{device_id}", tailnet_scope=False)

    def delete_device(self, device_id: str) -> dict:
        return self._request("DELETE", f"/device/{device_id}", tailnet_scope=False)

    def expire_device_key(self, device_id: str) -> dict:
        return self._request("POST", f"/device/{device_id}/expire", tailnet_scope=False)

    def get_device_routes(self, device_id: str) -> dict:
        return self._request("GET", f"/device/{device_id}/routes", tailnet_scope=False)

    def set_device_routes(self, device_id: str, routes: list[str]) -> dict:
        return self._request("POST", f"/device/{device_id}/routes", tailnet_scope=False, json={"routes": routes})

    def authorize_device(self, device_id: str, authorized: bool) -> dict:
        return self._request("POST", f"/device/{device_id}/authorized", tailnet_scope=False, json={"authorized": authorized})

    def set_device_name(self, device_id: str, name: str) -> dict:
        return self._request("POST", f"/device/{device_id}/name", tailnet_scope=False, json={"name": name})

    def set_device_tags(self, device_id: str, tags: list[str]) -> dict:
        return self._request("POST", f"/device/{device_id}/tags", tailnet_scope=False, json={"tags": tags})

    def update_device_key(self, device_id: str, key_expiry_disabled: bool) -> dict:
        return self._request("POST", f"/device/{device_id}/key", tailnet_scope=False, json={"keyExpiryDisabled": key_expiry_disabled})

    def set_device_ip(self, device_id: str, ipv4: str) -> dict:
        return self._request("POST", f"/device/{device_id}/ip", tailnet_scope=False, json={"ipv4": ipv4})

    def get_device_posture_attributes(self, device_id: str) -> dict:
        return self._request("GET", f"/device/{device_id}/attributes", tailnet_scope=False)

    def set_custom_device_posture_attribute(self, device_id: str, key: str, value, expiry: str = "", comment: str = "") -> dict:
        body = {"value": value}
        if expiry:
            body["expiry"] = expiry
        if comment:
            body["comment"] = comment
        return self._request("POST", f"/device/{device_id}/attributes/{key}", tailnet_scope=False, json=body)

    def delete_custom_device_posture_attribute(self, device_id: str, key: str) -> dict:
        return self._request("DELETE", f"/device/{device_id}/attributes/{key}", tailnet_scope=False)

    # ── Device invites ──
    def list_device_invites(self, device_id: str) -> list:
        resp = self._request("GET", f"/device/{device_id}/device-invites", tailnet_scope=False)
        return resp if isinstance(resp, list) else (resp or [])

    def create_device_invites(self, device_id: str, invites: list[dict]) -> list:
        return self._request("POST", f"/device/{device_id}/device-invites", tailnet_scope=False, json=invites)

    def get_device_invite(self, invite_id: str) -> dict:
        return self._request("GET", f"/device-invites/{invite_id}", tailnet_scope=False)

    def delete_device_invite(self, invite_id: str) -> dict:
        return self._request("DELETE", f"/device-invites/{invite_id}", tailnet_scope=False)

    def resend_device_invite(self, invite_id: str) -> dict:
        return self._request("POST", f"/device-invites/{invite_id}/resend", tailnet_scope=False)

    def accept_device_invite(self, invite: str) -> dict:
        return self._request("POST", "/device-invites/-/accept", tailnet_scope=False, json={"invite": invite})

    # ── DNS ──
    def set_dns_nameservers(self, nameservers: list[str]) -> dict:
        return self._request("POST", "/dns/nameservers", json={"dns": nameservers})

    def list_dns_nameservers(self) -> list:
        data = self._request("GET", "/dns/nameservers")
        return data.get("dns", [])

    def get_dns_preferences(self) -> dict:
        return self._request("GET", "/dns/preferences")

    def set_dns_preferences(self, magic_dns: bool = True) -> dict:
        return self._request("POST", "/dns/preferences", json={"magicDns": magic_dns})

    def get_dns_search_paths(self) -> list[str]:
        data = self._request("GET", "/dns/searchpaths")
        return data.get("searchPaths", [])

    def set_dns_search_paths(self, search_paths: list[str]) -> dict:
        return self._request("POST", "/dns/searchpaths", json={"searchPaths": search_paths})

    def get_split_dns(self) -> dict:
        return self._request("GET", "/dns/split-dns")

    def set_split_dns(self, domain: str, nameservers: list[str]) -> dict:
        return self._request("PUT", f"/dns/split-dns/{domain}", json={"dns": nameservers})

    def delete_split_dns(self, domain: str) -> dict:
        return self._request("DELETE", f"/dns/split-dns/{domain}")

    def get_dns_configuration(self) -> dict:
        return self._request("GET", "/dns/configuration")

    def set_dns_configuration(self, config: dict) -> dict:
        return self._request("PUT", "/dns/configuration", json=config)

    # ── Auth Keys ──
    def get_keys(self) -> list[dict]:
        data = self._request("GET", "/keys")
        return data.get("keys", [])

    def create_auth_key(self, **key_config) -> dict:
        return self._request("POST", "/keys", json=key_config)

    def get_key(self, key_id: str) -> dict:
        return self._request("GET", f"/keys/{key_id}")

    def delete_key(self, key_id: str) -> dict:
        return self._request("DELETE", f"/keys/{key_id}")

    # ── Users ──
    def list_users(self) -> list[dict]:
        data = self._request("GET", "/users")
        return data.get("users", [])

    def get_user(self, user_id: str) -> dict:
        return self._request("GET", f"/users/{user_id}", tailnet_scope=False)

    def set_user_role(self, user_id: str, role: str) -> dict:
        return self._request("POST", f"/users/{user_id}/role", tailnet_scope=False, json={"role": role})

    def approve_user(self, user_id: str) -> dict:
        return self._request("POST", f"/users/{user_id}/approve", tailnet_scope=False)

    def suspend_user(self, user_id: str) -> dict:
        return self._request("POST", f"/users/{user_id}/suspend", tailnet_scope=False)

    def restore_user(self, user_id: str) -> dict:
        return self._request("POST", f"/users/{user_id}/restore", tailnet_scope=False)

    def delete_user(self, user_id: str) -> dict:
        return self._request("POST", f"/users/{user_id}/delete", tailnet_scope=False)

    # ── User invites ──
    def list_user_invites(self) -> list:
        resp = self._request("GET", "/user-invites")
        return resp if isinstance(resp, list) else (resp or [])

    def create_user_invites(self, invites: list[dict]) -> list:
        return self._request("POST", "/user-invites", json=invites)

    def get_user_invite(self, invite_id: str) -> dict:
        return self._request("GET", f"/user-invites/{invite_id}", tailnet_scope=False)

    def delete_user_invite(self, invite_id: str) -> dict:
        return self._request("DELETE", f"/user-invites/{invite_id}", tailnet_scope=False)

    def resend_user_invite(self, invite_id: str) -> dict:
        return self._request("POST", f"/user-invites/{invite_id}/resend", tailnet_scope=False)

    # ── Logging ──
    def list_configuration_audit_logs(self, start: str, end: str, **filters) -> dict:
        params = {"start": start, "end": end, **filters}
        return self._request("GET", "/logging/configuration", params=params)

    def list_network_flow_logs(self, start: str, end: str) -> dict:
        params = {"start": start, "end": end}
        return self._request("GET", "/logging/network", params=params)

    def get_log_streaming_config(self, log_type: str) -> dict:
        return self._request("GET", f"/logging/{log_type}/stream")

    def set_log_streaming_config(self, log_type: str, config: dict) -> dict:
        return self._request("PUT", f"/logging/{log_type}/stream", json=config)

    def get_log_streaming_status(self, log_type: str) -> dict:
        return self._request("GET", f"/logging/{log_type}/stream/status")

    # ── Contacts ──
    def get_contacts(self) -> dict:
        data = self._request("GET", "/contacts")
        return data.get("contacts", [])

    def update_contact(self, contact_type: str, data: dict) -> dict:
        return self._request("PATCH", f"/contacts/{contact_type}", json=data)

    def resend_contact_verification(self, contact_type: str) -> dict:
        return self._request("POST", f"/contacts/{contact_type}/resend-verification-email")

    # ── Webhooks ──
    def list_webhooks(self) -> list:
        resp = self._request("GET", "/webhooks")
        if isinstance(resp, dict):
            hooks = resp.get("webhooks")
            return hooks if isinstance(hooks, list) else []
        return []

    def create_webhook(self, config: dict) -> dict:
        return self._request("POST", "/webhooks", json=config)

    def get_webhook(self, endpoint_id: str) -> dict:
        return self._request("GET", f"/webhooks/{endpoint_id}", tailnet_scope=False)

    def update_webhook(self, endpoint_id: str, config: dict) -> dict:
        return self._request("PUT", f"/webhooks/{endpoint_id}", tailnet_scope=False, json=config)

    def delete_webhook(self, endpoint_id: str) -> dict:
        return self._request("DELETE", f"/webhooks/{endpoint_id}", tailnet_scope=False)

    def test_webhook(self, endpoint_id: str) -> dict:
        return self._request("POST", f"/webhooks/{endpoint_id}/test", tailnet_scope=False)

    def rotate_webhook_secret(self, endpoint_id: str) -> dict:
        return self._request("POST", f"/webhooks/{endpoint_id}/rotate", tailnet_scope=False)

    # ── Device Posture ──
    def list_posture_integrations(self) -> list:
        data = self._request("GET", "/posture/integrations")
        if isinstance(data, dict):
            return data.get("integrations", [])
        return data or []

    def create_posture_integration(self, config: dict) -> dict:
        return self._request("POST", "/posture/integrations", json=config)

    def get_posture_integration(self, integration_id: str) -> dict:
        return self._request("GET", f"/posture/integrations/{integration_id}", tailnet_scope=False)

    def update_posture_integration(self, integration_id: str, config: dict) -> dict:
        return self._request("PUT", f"/posture/integrations/{integration_id}", tailnet_scope=False, json=config)

    def delete_posture_integration(self, integration_id: str) -> dict:
        return self._request("DELETE", f"/posture/integrations/{integration_id}", tailnet_scope=False)

    def batch_update_posture_attributes(self, nodes: dict, comment: str = "") -> dict:
        body: dict[str, dict] = {"nodes": nodes}
        if comment:
            body["comment"] = comment
        return self._request("PATCH", "/device-attributes", json=body)

    # ── Tailnet settings ──
    def get_tailnet_settings(self) -> dict:
        return self._request("GET", "/settings")

    def update_tailnet_settings(self, settings: dict) -> dict:
        return self._request("PATCH", "/settings", json=settings)

    # ── Services ──
    def list_services(self) -> list:
        resp = self._request("GET", "/services")
        if isinstance(resp, dict):
            return resp.get("vipServices", []) or resp.get("services", [])
        return resp or []

    def get_service(self, service_name: str) -> dict:
        return self._request("GET", f"/services/{service_name}")

    def list_service_devices(self, service_name: str) -> list[dict]:
        return self._request("GET", f"/services/{service_name}/devices")

    def get_service_device_approval(self, service_name: str, device_id: str) -> dict:
        return self._request("GET", f"/services/{service_name}/device/{device_id}/approved")

    def approve_service_device(self, service_name: str, device_id: str, approved: bool = True) -> dict:
        if approved:
            return self._request("POST", f"/services/{service_name}/device/{device_id}/approved")
        return self._request("DELETE", f"/services/{service_name}/device/{device_id}/approved", tailnet_scope=False)

    # ── AWS ──
    def create_aws_external_id(self) -> dict:
        return self._request("POST", "/aws-external-id")

    def validate_aws_trust_policy(self, ext_id: str) -> dict:
        return self._request("GET", f"/aws-external-id/{ext_id}/validate-aws-trust-policy")
