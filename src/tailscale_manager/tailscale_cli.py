import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class TailscaleStatus:
    online: bool = False
    device_name: str = ""
    tailscale_ip: list[str] = field(default_factory=list)
    version: str = ""
    current_user: str = ""
    peers: list[dict] = field(default_factory=list)
    self_info: dict = field(default_factory=dict)
    magic_dns: bool = False
    health: list[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, raw: dict) -> "TailscaleStatus":
        self = cls()
        sd = raw.get("Self", {})
        self.device_name = sd.get("DNSName", "").rstrip(".")
        self.tailscale_ip = sd.get("TailscaleIPs", [])
        self.version = raw.get("Version", "")
        self.current_user = raw.get("CurrentTailnet", {}).get("Name", "")
        self.magic_dns = raw.get("MagicDNSSuffix", "") != ""
        self.health = raw.get("Health", [])

        self.self_info = {
            "id": sd.get("ID", ""),
            "name": self.device_name.split(".")[0] if "." in self.device_name else self.device_name,
            "dns_name": self.device_name,
            "ip": self.tailscale_ip,
            "os": sd.get("OS", ""),
            "online": sd.get("Online", True),
            "relay": sd.get("Relay", ""),
            "rx_bytes": sd.get("RxBytes", 0),
            "tx_bytes": sd.get("TxBytes", 0),
            "latency": {},
            "in_network_map": sd.get("InNetworkMap", True),
            "last_seen": sd.get("LastSeen", ""),
            "exit_node": sd.get("ExitNode", False),
            "exit_node_allow": sd.get("ExitNodeOption", False),
        }

        peers = []
        for key, peer in raw.get("Peer", {}).items():
            name = peer.get("DNSName", "").rstrip(".")
            peers.append(
                {
                    "id": key,
                    "name": name,
                    "dns_name": name,
                    "ip": peer.get("TailscaleIPs", []),
                    "os": peer.get("OS", ""),
                    "online": peer.get("Online", False),
                    "relay": peer.get("Relay", ""),
                    "rx_bytes": peer.get("RxBytes", 0),
                    "tx_bytes": peer.get("TxBytes", 0),
                    "latency": peer.get("Latency", {}),
                    "in_network_map": peer.get("InNetworkMap", False),
                    "last_seen": peer.get("LastSeen", ""),
                    "exit_node": peer.get("ExitNode", False),
                    "exit_node_allow": peer.get("ExitNodeAllow", False),
                }
            )
        peers.sort(key=lambda p: p["name"].lower())
        self.peers = peers
        self.online = True
        return self


@dataclass
class ServeConfig:
    enabled: bool = False
    routes: list[dict] = field(default_factory=list)

    @classmethod
    def from_json(cls, raw: dict) -> "ServeConfig":
        self = cls()
        self.enabled = bool(raw)
        for source_path, target in raw.get("TCP", {}).get("443", {}).items():
            self.routes.append(
                {"type": "tcp", "source": source_path, "target": target}
            )
        for source_path, target in raw.get("Web", {}).items():
            for srv in target.get("Handlers", []):
                self.routes.append(
                    {"type": "web", "source": source_path, "target": srv}
                )
        return self


class TailscaleCLIError(Exception):
    pass


class TailscaleCLI:
    def __init__(self, tailscale_path: str = "tailscale"):
        self._path = tailscale_path

    def _run(self, *args: str, timeout: int = 15) -> str:
        try:
            result = subprocess.run(
                [self._path, *args],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode != 0:
                raise TailscaleCLIError(result.stderr.strip() or result.stdout.strip())
            return result.stdout.strip()
        except FileNotFoundError:
            raise TailscaleCLIError("tailscale binary not found on PATH")
        except subprocess.TimeoutExpired:
            raise TailscaleCLIError("tailscale command timed out")

    def _run_json(self, *args: str, timeout: int = 15) -> dict:
        out = self._run(*args, "--json", timeout=timeout)
        if not out:
            return {}
        return json.loads(out)

    def status(self) -> TailscaleStatus:
        raw = self._run_json("status")
        return TailscaleStatus.from_json(raw)

    def up(
        self,
        accept_routes: bool = False,
        accept_dns: bool = True,
        exit_node: str = "",
        exit_node_allow: bool = True,
        advertise_routes: str = "",
        advertise_tags: str = "",
        ssh: bool = True,
    ) -> str:
        args = ["up", "--accept-dns=false" if not accept_dns else "--accept-dns"]
        if accept_routes:
            args.append("--accept-routes")
        if exit_node:
            args.extend(["--exit-node", exit_node])
            if exit_node_allow:
                args.append("--exit-node-allow-lan-access")
        if advertise_routes:
            args.extend(["--advertise-routes", advertise_routes])
        if advertise_tags:
            args.extend(["--advertise-tags", advertise_tags])
        if ssh:
            args.append("--ssh")
        return self._run(*args, timeout=60)

    def down(self) -> str:
        return self._run("down")

    def logout(self) -> str:
        return self._run("logout")

    def version(self) -> str:
        return self._run("version")

    def whois(self, ip: str) -> dict:
        return self._run_json("whois", ip)

    def ping(self, host: str, timeout: int = 10) -> str:
        return self._run("ping", "--c", "3", host, timeout=timeout)

    def netcheck(self) -> dict:
        return self._run_json("netcheck")

    def serve_status(self) -> ServeConfig:
        raw = self._run_json("serve", "status")
        return ServeConfig.from_json(raw)

    def funnel_status(self) -> dict:
        raw = self._run_json("funnel", "status")
        return ServeConfig.from_json(raw)

    def serve_set(self, source: str, target: str, on: bool = True) -> str:
        cmd = "on" if on else "off"
        return self._run("serve", cmd, "--bg", f"https://{source}", f"http://{target}", timeout=30)

    def funnel_set(self, source: str, target: str, on: bool = True) -> str:
        cmd = "on" if on else "off"
        return self._run("funnel", cmd, "--bg", f"https://{source}", f"http://{target}", timeout=30)

    def serve_remove(self, source: str) -> str:
        return self._run("serve", "off", f"https://{source}")

    def file_send(self, file_path: str, target_device: str) -> str:
        return self._run("file", "send", file_path, target_device)

    def cert(self, domain: str) -> str:
        return self._run("cert", domain, timeout=60)

    def switch(self, profile: str) -> str:
        return self._run("switch", profile)

    def whoami(self) -> dict:
        return self._run_json("whoami")

    def bug_report(self) -> str:
        return self._run("bugreport")

    def licenses(self) -> str:
        return self._run("licenses")


def get_tailscale_path() -> str:
    if Path("C:\\Program Files\\Tailscale\\tailscale.exe").exists():
        return "C:\\Program Files\\Tailscale\\tailscale.exe"
    return "tailscale"
