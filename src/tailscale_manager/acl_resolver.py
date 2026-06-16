import ipaddress
from .api_client import TailscaleAPIClient, TailscaleAPIError


class ACLResolver:
    def __init__(self, api: TailscaleAPIClient):
        self._api = api
        self._acl: dict = {}
        self._devices: list[dict] = []
        self._groups: dict[str, list[str]] = {}
        self._dev_by_fqdn: dict[str, dict] = {}
        self._loaded = False

    def fetch(self):
        try:
            self._acl = self._api.get_acl()
            self._devices = self._api.list_devices()
            self._groups = self._acl.get("groups", {})
            for d in self._devices:
                fqdn = d.get("name", "").rstrip(".").lower()
                self._dev_by_fqdn[fqdn] = d
            self._loaded = True
        except TailscaleAPIError:
            self._loaded = False

    @property
    def loaded(self) -> bool:
        return self._loaded

    def _resolve_group(self, group: str) -> set[str]:
        members = set()
        for m in self._groups.get(group, []):
            members.add(m.lower())
        return members

    def _peer_dev(self, peer: dict) -> dict | None:
        fqdn = peer.get("dns_name", "").lower().rstrip(".")
        return self._dev_by_fqdn.get(fqdn)

    def _peer_tags(self, peer: dict) -> list[str]:
        dev = self._peer_dev(peer)
        if dev:
            return [t.lower() for t in dev.get("tags", [])]
        return []

    def _peer_user(self, peer: dict) -> str:
        dev = self._peer_dev(peer)
        if dev:
            return dev.get("user", "").lower()
        return ""

    def _match_src(self, entry: str, peer: dict) -> bool:
        e = entry.lower().rstrip(".")

        if e in ("*", "autogroup:members"):
            return True

        if e == "autogroup:self":
            return True

        if e == "autogroup:admin":
            return True

        if e.startswith("tag:"):
            return e in self._peer_tags(peer)

        if e.startswith("group:"):
            resolved = self._resolve_group(e)
            peer_tags = self._peer_tags(peer)
            peer_user = self._peer_user(peer)
            for m in resolved:
                if m.startswith("tag:") and m in peer_tags:
                    return True
                if m == peer_user:
                    return True
            return False

        if "@" in e:
            return e == self._peer_user(peer)

        try:
            return e in [ip.lower() for ip in peer.get("ip", [])]
        except (ValueError, TypeError):
            pass

        peer_name = peer.get("name", "").lower().rstrip(".")
        peer_dns = peer.get("dns_name", "").lower().rstrip(".")
        return e in (peer_name, peer_dns)

    def _match_dst(self, entry: str, peer: dict) -> bool:
        host = entry
        if ":" in entry:
            host, _port = entry.rsplit(":", 1)
        host = host.lower().rstrip(".")

        if host == "*":
            return True

        if host.startswith("tag:"):
            return host in self._peer_tags(peer)

        if host.startswith("group:"):
            resolved = self._resolve_group(host)
            peer_tags = self._peer_tags(peer)
            peer_user = self._peer_user(peer)
            for m in resolved:
                if m.startswith("tag:") and m in peer_tags:
                    return True
                if m == peer_user:
                    return True
            return False

        if host.startswith("autogroup:"):
            return True

        if "@" in host:
            return host == self._peer_user(peer)

        try:
            net = ipaddress.ip_network(host, strict=False)
            for ip_str in peer.get("ip", []):
                try:
                    if ipaddress.ip_address(ip_str) in net:
                        return True
                except ValueError:
                    pass
        except ValueError:
            pass

        try:
            return host in [ip.lower() for ip in peer.get("ip", [])]
        except (ValueError, TypeError):
            pass

        peer_name = peer.get("name", "").lower().rstrip(".")
        peer_dns = peer.get("dns_name", "").lower().rstrip(".")
        return host in (peer_name, peer_dns)

    def for_peer(self, peer: dict) -> list[dict]:
        if not self._loaded:
            return []
        results = []
        for rule in self._acl.get("acls", []):
            srcs = rule.get("src", [])
            dsts = rule.get("dst", [])
            action = rule.get("action", "accept")
            is_src = any(self._match_src(s, peer) for s in srcs)
            is_dst = any(self._match_dst(d, peer) for d in dsts)
            if is_src:
                results.append({"dir": "out", "action": action, "dsts": dsts})
            if is_dst:
                results.append({"dir": "in", "action": action, "srcs": srcs})
        return results

    def format_rule(self, rule: dict) -> str:
        if rule["dir"] == "out":
            dsts = ", ".join(rule.get("dsts", []))
            return f"\u2192 {dsts}"
        srcs = ", ".join(rule.get("srcs", []))
        return f"\u2190 {srcs}"
