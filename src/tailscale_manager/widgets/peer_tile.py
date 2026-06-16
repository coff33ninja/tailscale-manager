import flet as ft
from datetime import datetime, timezone
from ..constants import STATUS_COLORS


def _format_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024**2:
        return f"{b/1024:.1f} KB"
    elif b < 1024**3:
        return f"{b/1024**2:.1f} MB"
    return f"{b/1024**3:.1f} GB"


def _relative_time(ts: str) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        days = diff.days
        seconds = diff.seconds
        if days > 30:
            return f"{days // 30}mo ago"
        elif days > 0:
            return f"{days}d ago"
        elif seconds >= 3600:
            return f"{seconds // 3600}h ago"
        elif seconds >= 60:
            return f"{seconds // 60}m ago"
        return "just now"
    except Exception:
        return ts


def peer_tile(peer: dict, services: list | None = None, on_click=None, on_open_service=None, acls: list[dict] | None = None) -> ft.Container:
    is_online = peer.get("online", False)
    status = "online" if is_online else "offline"
    dot_color = STATUS_COLORS[status]

    rx = peer.get("rx_bytes", 0)
    tx = peer.get("tx_bytes", 0)
    latency = peer.get("latency", {})

    lat_ms = ""
    relay = peer.get("relay", "")
    for val in latency.values():
        if isinstance(val, dict) and "latency" in val:
            lat_ms = f"{val['latency']:.0f}ms"
            break

    ip_str = ", ".join(peer.get("ip", []))
    os_map = {
        "windows": (ft.Icons.DESKTOP_WINDOWS, "Windows"),
        "macos": (ft.Icons.APPLE, "macOS"),
        "ios": (ft.Icons.PHONE_IPHONE, "iOS"),
        "ipados": (ft.Icons.TABLET, "iPadOS"),
        "iphone": (ft.Icons.PHONE_IPHONE, "iPhone"),
        "ipad": (ft.Icons.TABLET, "iPad"),
        "tvos": (ft.Icons.TV, "tvOS"),
        "visionos": (ft.Icons.VISIBILITY, "visionOS"),
        "android": (ft.Icons.ANDROID, "Android"),
        "linux": (ft.Icons.TERMINAL, "Linux"),
        "freebsd": (ft.Icons.TERMINAL, "FreeBSD"),
        "openbsd": (ft.Icons.TERMINAL, "OpenBSD"),
    }
    os_raw = peer.get("os", "").lower()
    os_icon, os_label = os_map.get(os_raw, (ft.Icons.DEVICE_UNKNOWN, os_raw or "Unknown"))

    exit_node = peer.get("exit_node", False)
    exit_node_allow = peer.get("exit_node_allow", False)
    in_network = peer.get("in_network_map", True)
    last_seen = peer.get("last_seen", "")
    peer_id = peer.get("id", "")

    acl_row = None
    if acls:
        chips = []
        for i, r in enumerate(acls):
            if i > 4:
                chips.append(ft.Text(f"+{len(acls)-4}", size=10, color=ft.Colors.GREY_500))
                break
            arrow = "\u2192" if r["dir"] == "out" else "\u2190"
            labels = ", ".join(r.get("dsts", r.get("srcs", [])))
            color = ft.Colors.GREEN_400 if r["action"] == "accept" else ft.Colors.RED_400
            chips.append(
                ft.Container(
                    content=ft.Text(f"{arrow} {labels}", size=9, color=color),
                    padding=ft.Padding(left=4, top=1, right=4, bottom=1),
                    border_radius=4,
                    bgcolor=ft.Colors.with_opacity(0.12, color),
                )
            )
        acl_row = ft.Row(chips, spacing=4, wrap=True)

    name_parts = [ft.Text(peer.get("name", ""), size=15, weight=ft.FontWeight.W_600)]

    if exit_node:
        label = "Exit Node"
        if exit_node_allow:
            label += " (LAN)"
        name_parts.append(
            ft.Container(
                content=ft.Text(label, size=9, color=ft.Colors.AMBER_300),
                padding=ft.Padding(left=6, top=2, right=6, bottom=2),
                border_radius=6,
                bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.AMBER),
            )
        )

    if not in_network:
        name_parts.append(
            ft.Icon(ft.Icons.WARNING_AMBER, size=14, color=ft.Colors.AMBER_400, tooltip="Not in network map")
        )

    name_parts.append(ft.Container(width=8, height=8, border_radius=4, bgcolor=dot_color))

    name_row = ft.Row(name_parts, spacing=6)

    relay_lat = ""
    if is_online:
        parts = []
        if relay:
            parts.append(relay)
        if lat_ms:
            parts.append(lat_ms)
        relay_lat = " \u00b7 ".join(parts) if parts else ""
    else:
        rt = _relative_time(last_seen)
        relay_lat = f"Last seen: {rt}" if rt else ""

    info_row = ft.Row(
        [
            ft.Text(ip_str, size=12, color=ft.Colors.GREY_400),
            ft.Text(f"\u00b7 {os_label}", size=11, color=ft.Colors.GREY_500),
            ft.Container(expand=True),
            ft.Text(relay_lat, size=11, color=ft.Colors.GREY_500),
        ],
        spacing=2,
    )

    service_row = ft.Row(spacing=6, wrap=True) if services else None
    if services:
        for svc in services:
            btn = ft.IconButton(
                icon=svc.get("icon", ft.Icons.DNS),
                tooltip=f"{svc['name']} ({svc['port']})",
                icon_size=18,
                height=30,
                width=30,
                on_click=lambda _, s=svc: on_open_service(peer.get("ip", [""])[0], s) if on_open_service else None,
            )
            service_row.controls.append(btn)

    os_icon_container = ft.Container(
        content=ft.Icon(os_icon, size=22, color=ft.Colors.GREY_300),
        width=44, height=44,
        border_radius=22,
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY),
        alignment=ft.Alignment.CENTER,
        tooltip=f"{os_label}\n{peer_id}" if peer_id else os_label,
    )

    body = ft.Column(
        [
            ft.Row(
                [
                    os_icon_container,
                    ft.Column(
                        [
                            name_row,
                            info_row,
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                f"\u2193 {_format_bytes(rx)}  \u2191 {_format_bytes(tx)}",
                                size=11, color=ft.Colors.GREY_400,
                            ),
                        ],
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        spacing=4,
    )

    if service_row:
        body.controls.append(
            ft.Container(
                content=service_row,
                padding=ft.Padding(left=0, top=4, right=0, bottom=0),
            )
        )

    if acl_row:
        body.controls.append(
            ft.Container(
                content=acl_row,
                padding=ft.Padding(left=0, top=4, right=0, bottom=0),
            )
        )

    return ft.Container(
        content=body,
        padding=ft.Padding(left=16, top=12, right=16, bottom=12),
        border_radius=10,
        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
        border=ft.Border(
            top=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
            right=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
            bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
            left=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
        ),
        on_click=on_click,
    )
