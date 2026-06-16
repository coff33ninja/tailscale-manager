import socket
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import flet as ft

SERVICES: list[tuple[int, str, int, Optional[str]]] = [
    (22, "SSH", ft.Icons.TERMINAL, "ssh://{ip}"),
    (80, "HTTP", ft.Icons.HTTP, "http://{ip}"),
    (443, "HTTPS", ft.Icons.HTTPS, "https://{ip}"),
    (3389, "RDP", ft.Icons.COMPUTER, "rdp://{ip}"),
    (7070, "RustDesk", ft.Icons.BUG_REPORT, None),
    (6568, "AnyDesk", ft.Icons.SETTINGS_REMOTE, None),
    (5900, "VNC", ft.Icons.VIBRATION, "vnc://{ip}"),
    (3000, "Gitea", ft.Icons.CODE, "http://{ip}:3000"),
    (8123, "HA", ft.Icons.HOME, "http://{ip}:8123"),
    (8096, "Jellyfin", ft.Icons.MOVIE, "http://{ip}:8096"),
    (32400, "Plex", ft.Icons.PLAY_CIRCLE, "http://{ip}:32400/web"),
    (9090, "Cockpit", ft.Icons.DASHBOARD, "https://{ip}:9090"),
    (9443, "Portainer", ft.Icons.STORAGE, "https://{ip}:9443"),
    (1880, "Node-RED", ft.Icons.ALT_ROUTE, "http://{ip}:1880"),
    (8080, "Web", ft.Icons.PUBLIC, "http://{ip}:8080"),
    (8443, "Web SSL", ft.Icons.LOCK, "https://{ip}:8443"),
]


def _try_port(ip: str, port: int, timeout: float = 1.0) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((ip, port))
        s.close()
        return result == 0
    except Exception:
        return False


def scan_peer(ip: str, timeout: float = 1.0) -> list[dict]:
    results: list[dict] = []
    if not ip:
        return results
    with ThreadPoolExecutor(max_workers=min(len(SERVICES), 20)) as pool:
        fut = {pool.submit(_try_port, ip, p, timeout): p for p, _, _, _ in SERVICES}
        for f in as_completed(fut):
            port = fut[f]
            try:
                if f.result():
                    for p, name, icon, url in SERVICES:
                        if p == port:
                            results.append({"port": port, "name": name, "icon": icon, "url": url})
                            break
                    if port not in [r["port"] for r in results]:
                        results.append({"port": port, "name": str(port), "icon": ft.Icons.DNS, "url": f"http://{ip}:{port}"})
            except Exception:
                pass
    results.sort(key=lambda r: r["port"])
    return results


def open_service(ip: str, svc: dict):
    url = svc.get("url")
    if url:
        webbrowser.open(url.format(ip=ip))
