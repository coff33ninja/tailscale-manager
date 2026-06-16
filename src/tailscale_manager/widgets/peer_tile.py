import flet as ft
from ..constants import STATUS_COLORS


def _format_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024**2:
        return f"{b/1024:.1f} KB"
    elif b < 1024**3:
        return f"{b/1024**2:.1f} MB"
    return f"{b/1024**3:.1f} GB"


def peer_tile(peer: dict, services: list | None = None, on_click=None, on_open_service=None) -> ft.Container:
    is_online = peer.get("online", False)
    status = "online" if is_online else "offline"
    dot_color = STATUS_COLORS[status]

    rx = peer.get("rx_bytes", 0)
    tx = peer.get("tx_bytes", 0)
    latency = peer.get("latency", {})

    lat_ms = ""
    for val in latency.values():
        if isinstance(val, dict) and "latency" in val:
            lat_ms = f"{val['latency']:.0f}ms"
            break

    ip_str = ", ".join(peer.get("ip", []))
    os_icon = {"windows": "WINDOWS", "macos": "APPLE", "linux": "TERMINAL", "android": "ANDROID", "ios": "PHONE_IPHONE"}.get(
        peer.get("os", "").lower(), "DEVICE_UNKNOWN"
    )

    service_row = ft.Row(spacing=6, wrap=True) if services else None
    if services:
        for svc in services:
            btn = ft.IconButton(
                icon=svc.get("icon", "DNS"),
                tooltip=f"{svc['name']} ({svc['port']})",
                icon_size=18,
                height=30,
                width=30,
                on_click=lambda _, s=svc: on_open_service(peer.get("ip", [""])[0], s) if on_open_service else None,
            )
            service_row.controls.append(btn)

    body = ft.Column(
        [
            ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(os_icon, size=22, color=ft.Colors.GREY_300),
                        width=44, height=44,
                        border_radius=22,
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY),
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(peer.get("name", ""), size=15, weight=ft.FontWeight.W_600),
                                    ft.Container(width=8, height=8, border_radius=4, bgcolor=dot_color),
                                ],
                                spacing=6,
                            ),
                            ft.Text(ip_str, size=12, color=ft.Colors.GREY_400),
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
                            ft.Text(lat_ms, size=11, color=ft.Colors.GREY_500),
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
