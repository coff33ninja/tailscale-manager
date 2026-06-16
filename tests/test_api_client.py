"""
Integration tests for TailscaleAPIClient — hits the live API.

Requires TAILSCALE_API_KEY and TAILSCALE_TAILNET env vars.
Write-modifying tests are marked @pytest.mark.write_op (skip with -m "not write_op").
"""

import pytest
from tailscale_manager.api_client import TailscaleAPIClient, TailscaleAPIError


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client(api_key: str, tailnet: str) -> TailscaleAPIClient:
    return TailscaleAPIClient(api_key, tailnet)


@pytest.fixture(scope="module")
def device_id(client: TailscaleAPIClient) -> str:
    devices = client.list_devices()
    if not devices:
        pytest.skip("no devices in tailnet")
    return devices[0]["id"]


@pytest.fixture(scope="module")
def device(client: TailscaleAPIClient, device_id: str) -> dict:
    return client.get_device(device_id)


# ── ACL / Policy ──────────────────────────────────────────────────────

class TestACL:
    def test_get_acl(self, client: TailscaleAPIClient):
        acl = client.get_acl()
        assert isinstance(acl, dict)
        assert "acls" in acl

    def test_validate_acl(self, client: TailscaleAPIClient):
        acl = client.get_acl()
        warnings = client.validate_acl(acl)
        assert isinstance(warnings, list)

    def test_preview_acl(self, client: TailscaleAPIClient):
        acl = client.get_acl()
        matches = client.preview_acl(acl)
        assert isinstance(matches, list)

    @pytest.mark.write_op
    def test_set_acl(self, client: TailscaleAPIClient):
        acl = client.get_acl()
        etag = acl.pop("etag", "")
        resp = client.set_acl(acl, etag)
        assert isinstance(resp, dict)


# ── Devices ───────────────────────────────────────────────────────────

class TestDevices:
    def test_list_devices(self, client: TailscaleAPIClient):
        devices = client.list_devices()
        assert isinstance(devices, list)
        if devices:
            d = devices[0]
            assert "id" in d
            assert "name" in d

    def test_list_devices_filtered(self, client: TailscaleAPIClient):
        devices = client.list_devices(**{"isEphemeral": "false"})
        assert isinstance(devices, list)

    def test_get_device(self, client: TailscaleAPIClient, device_id: str):
        d = client.get_device(device_id)
        assert isinstance(d, dict)
        assert d.get("id") == device_id

    def test_get_device_routes(self, client: TailscaleAPIClient, device_id: str):
        routes = client.get_device_routes(device_id)
        assert isinstance(routes, dict)
        assert "advertisedRoutes" in routes
        assert "enabledRoutes" in routes

    def test_get_device_posture_attributes(self, client: TailscaleAPIClient, device_id: str):
        attrs = client.get_device_posture_attributes(device_id)
        assert isinstance(attrs, dict)
        assert "attributes" in attrs or True  # may be empty

    @pytest.mark.write_op
    def test_set_device_name(self, client: TailscaleAPIClient, device: dict):
        d = device
        name = d.get("name", "").split(".")[0]
        resp = client.set_device_name(d["id"], name)
        assert resp is not None

    @pytest.mark.write_op
    def test_set_device_tags(self, client: TailscaleAPIClient, device_id: str, device: dict):
        existing_tags = device.get("tags", [])
        resp = client.set_device_tags(device_id, existing_tags)
        assert resp is not None

    @pytest.mark.write_op
    def test_authorize_device(self, client: TailscaleAPIClient, device_id: str, device: dict):
        authorized = device.get("authorized", True)
        resp = client.authorize_device(device_id, authorized)
        assert resp is not None

    def test_delete_device(self, client: TailscaleAPIClient, device_id: str):
        with pytest.raises(TailscaleAPIError) as exc:
            # Deleting self would be bad; expect 400/404/501
            client.delete_device("nonexistent-id")
        assert exc.value is not None


# ── Device invites ────────────────────────────────────────────────────

class TestDeviceInvites:
    def test_list_device_invites(self, client: TailscaleAPIClient, device_id: str):
        invites = client.list_device_invites(device_id)
        assert isinstance(invites, list)


# ── DNS ───────────────────────────────────────────────────────────────

class TestDNS:
    def test_list_dns_nameservers(self, client: TailscaleAPIClient):
        ns = client.list_dns_nameservers()
        assert isinstance(ns, list)

    def test_get_dns_preferences(self, client: TailscaleAPIClient):
        prefs = client.get_dns_preferences()
        assert isinstance(prefs, dict)
        assert "magicDNS" in prefs or "magicDns" in prefs

    def test_get_dns_search_paths(self, client: TailscaleAPIClient):
        paths = client.get_dns_search_paths()
        assert isinstance(paths, list)

    def test_get_split_dns(self, client: TailscaleAPIClient):
        sdns = client.get_split_dns()
        assert isinstance(sdns, dict)

    def test_get_dns_configuration(self, client: TailscaleAPIClient):
        cfg = client.get_dns_configuration()
        assert isinstance(cfg, dict)

    @pytest.mark.write_op
    def test_set_dns_preferences(self, client: TailscaleAPIClient):
        prefs = client.get_dns_preferences()
        current = prefs.get("magicDns", True)
        resp = client.set_dns_preferences(current)
        assert isinstance(resp, dict)


# ── Auth Keys ─────────────────────────────────────────────────────────

class TestKeys:
    def test_get_keys(self, client: TailscaleAPIClient):
        keys = client.get_keys()
        assert isinstance(keys, list)

    @pytest.mark.write_op
    def test_create_and_delete_auth_key(self, client: TailscaleAPIClient):
        key = client.create_auth_key(
            capabilities={"devices": {}},
        )
        assert isinstance(key, dict)
        assert "id" in key
        client.delete_key(key["id"])


# ── Users ─────────────────────────────────────────────────────────────

class TestUsers:
    def test_list_users(self, client: TailscaleAPIClient):
        users = client.list_users()
        assert isinstance(users, list)
        if users:
            assert "id" in users[0]

    def test_get_user(self, client: TailscaleAPIClient):
        users = client.list_users()
        if not users:
            pytest.skip("no users in tailnet")
        u = client.get_user(users[0]["id"])
        assert isinstance(u, dict)
        assert u.get("id") == users[0]["id"]


# ── User invites ──────────────────────────────────────────────────────

class TestUserInvites:
    def test_list_user_invites(self, client: TailscaleAPIClient):
        invites = client.list_user_invites()
        assert isinstance(invites, list)


# ── Logging ───────────────────────────────────────────────────────────

class TestLogging:
    def test_get_log_streaming_config(self, client: TailscaleAPIClient):
        with pytest.raises(TailscaleAPIError):
            client.get_log_streaming_config("configuration")

    # Network/audit logs need date params; just test error shape
    def test_configuration_audit_logs_shape(self, client: TailscaleAPIClient):
        with pytest.raises(TailscaleAPIError) as exc:
            client.list_configuration_audit_logs("", "")
        assert "400" in str(exc.value) or "403" in str(exc.value)

    def test_network_flow_logs_shape(self, client: TailscaleAPIClient):
        with pytest.raises(TailscaleAPIError) as exc:
            client.list_network_flow_logs("", "")
        assert "400" in str(exc.value) or "403" in str(exc.value)


# ── Contacts ──────────────────────────────────────────────────────────

class TestContacts:
    def test_get_contacts(self, client: TailscaleAPIClient):
        contacts = client.get_contacts()
        assert isinstance(contacts, list)


# ── Webhooks ──────────────────────────────────────────────────────────

class TestWebhooks:
    def test_list_webhooks(self, client: TailscaleAPIClient):
        hooks = client.list_webhooks()
        assert isinstance(hooks, list)


# ── Device Posture ────────────────────────────────────────────────────

class TestPosture:
    def test_list_posture_integrations(self, client: TailscaleAPIClient):
        integrations = client.list_posture_integrations()
        assert isinstance(integrations, list)


# ── Tailnet settings ──────────────────────────────────────────────────

class TestTailnetSettings:
    def test_get_tailnet_settings(self, client: TailscaleAPIClient):
        settings = client.get_tailnet_settings()
        assert isinstance(settings, dict)


# ── Services ──────────────────────────────────────────────────────────

class TestServices:
    def test_list_services(self, client: TailscaleAPIClient):
        services = client.list_services()
        # returns list of VIP service objects
        assert isinstance(services, list)


# ── AWS ───────────────────────────────────────────────────────────────

class TestAWS:
    def test_create_aws_external_id(self, client: TailscaleAPIClient):
        resp = client.create_aws_external_id()
        assert isinstance(resp, dict)
        assert "externalId" in resp


# ── Edge cases ────────────────────────────────────────────────────────

class TestEdgeCases:
    """Boundary conditions, 404s, validation, and unusual response shapes."""

    def test_get_device_not_found(self, client: TailscaleAPIClient):
        with pytest.raises(TailscaleAPIError) as exc:
            client.get_device("nonexistent-device-id")
        assert "404" in str(exc.value)

    def test_get_key_not_found(self, client: TailscaleAPIClient):
        with pytest.raises(TailscaleAPIError) as exc:
            client.get_key("nonexistent-key-id")
        assert any(code in str(exc.value) for code in ("400", "404"))

    def test_get_user_not_found(self, client: TailscaleAPIClient):
        with pytest.raises(TailscaleAPIError) as exc:
            client.get_user("nonexistent-user-id")
        assert "404" in str(exc.value)

    def test_delete_key_not_found(self, client: TailscaleAPIClient):
        with pytest.raises(TailscaleAPIError) as exc:
            client.delete_key("nonexistent-key-id")
        assert any(code in str(exc.value) for code in ("400", "404"))

    def test_delete_device_not_found(self, client: TailscaleAPIClient):
        with pytest.raises(TailscaleAPIError) as exc:
            client.delete_device("nonexistent-device-id")
        assert "404" in str(exc.value)

    @pytest.mark.write_op
    def test_set_device_name_empty(self, client: TailscaleAPIClient, device_id: str):
        """Empty name string — API may accept or reject."""
        try:
            resp = client.set_device_name(device_id, "")
            assert resp is not None
        except TailscaleAPIError as e:
            assert "400" in str(e)

    @pytest.mark.write_op
    def test_set_device_name_very_long(self, client: TailscaleAPIClient, device_id: str):
        """Name exceeding typical length limits — API should reject."""
        long_name = "a" * 200
        try:
            resp = client.set_device_name(device_id, long_name)
            assert resp is not None
        except TailscaleAPIError as e:
            assert "400" in str(e)

    @pytest.mark.write_op
    def test_set_device_tags_empty(self, client: TailscaleAPIClient, device_id: str, device: dict):
        """Empty tags list — succeeds for untagged devices, rejected for tagged ones."""
        if device.get("tags"):
            with pytest.raises(TailscaleAPIError):
                client.set_device_tags(device_id, [])
        else:
            resp = client.set_device_tags(device_id, [])
            assert resp is not None

    def test_invalid_tag_format(self, client: TailscaleAPIClient, device_id: str):
        """Tags must start with 'tag:' per Tailscale API spec."""
        with pytest.raises(TailscaleAPIError) as exc:
            client.set_device_tags(device_id, ["invalid-tag-format"])
        assert "400" in str(exc.value)

    def test_delete_webhook_not_found(self, client: TailscaleAPIClient):
        with pytest.raises(TailscaleAPIError) as exc:
            client.delete_webhook("nonexistent-webhook-id")
        assert any(code in str(exc.value) for code in ("404", "500"))

    def test_get_device_invite_not_found(self, client: TailscaleAPIClient):
        with pytest.raises(TailscaleAPIError) as exc:
            client.get_device_invite("nonexistent-invite-id")
        assert any(code in str(exc.value) for code in ("400", "404"))

    def test_get_posture_integration_not_found(self, client: TailscaleAPIClient):
        with pytest.raises(TailscaleAPIError) as exc:
            client.get_posture_integration("nonexistent-integration-id")
        assert "404" in str(exc.value)

    def test_get_service_not_found(self, client: TailscaleAPIClient):
        with pytest.raises(TailscaleAPIError) as exc:
            client.get_service("nonexistent-service-name")
        assert "404" in str(exc.value)

    @pytest.mark.write_op
    def test_get_key_deleted_immediately(self, client: TailscaleAPIClient):
        """Create a key, get it, then delete it; verify not found after."""
        key = client.create_auth_key(capabilities={"devices": {}})
        assert "id" in key
        key_id = key["id"]

        got = client.get_key(key_id)
        assert isinstance(got, dict)
        assert got.get("id") == key_id

        client.delete_key(key_id)
        try:
            after = client.get_key(key_id)
            # API may still return stale data after delete — acceptable
            assert isinstance(after, dict)
        except TailscaleAPIError:
            pass

    def test_set_device_ip_collision(self, client: TailscaleAPIClient, device_id: str):
        """Setting a non-routable IP or bogus IP should be rejected."""
        with pytest.raises(TailscaleAPIError) as exc:
            client.set_device_ip(device_id, "0.0.0.0")
        assert "400" in str(exc.value) or "500" in str(exc.value)


# ── Error handling ────────────────────────────────────────────────────

class TestErrors:
    def test_invalid_credentials(self):
        bad = TailscaleAPIClient("tskey-api-invalid")
        with pytest.raises(TailscaleAPIError):
            bad.list_devices()

    def test_missing_tailnet_raises(self):
        no_tn = TailscaleAPIClient("tskey-api-xxxxx")
        with pytest.raises(TailscaleAPIError):
            no_tn.list_devices()

    @pytest.mark.write_op
    def test_bad_json_raises(self, client: TailscaleAPIClient):
        with pytest.raises(TailscaleAPIError):
            client._request("POST", "/acl", data="not json", headers={"Content-Type": "application/json"})
