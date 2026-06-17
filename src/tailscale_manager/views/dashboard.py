import threading
import flet as ft
from ..api_client import TailscaleAPIClient, TailscaleAPIError
from ..config import load as load_config
from ..tailscale_cli import TailscaleCLI, TailscaleCLIError
from ..widgets.loading import loading_view
from ..widgets.status_card import status_card

_RED = "#FF5252"
_WHITE = "#FFFFFF"
_GREY = "#9E9E9E"
_CARD_BG = "#2A2A3E"
_BORDER = "#3A3A5E"
_WARN = "#FFB74D"


class DashboardView(ft.Column):
    def __init__(self, cli: TailscaleCLI, api=None):
        super().__init__(expand=True, spacing=12)
        self.cli = cli
        self.api = api
        self._loaded = False
        self._content_ref = ft.Ref[ft.Column]()

        self.controls = [
            ft.Text("Dashboard", size=28, weight=ft.FontWeight.BOLD, color=_WHITE),
            ft.Text("Tailscale connection overview", size=13, color=_GREY),
            ft.Divider(height=20, color=_BORDER),
            ft.Column(ref=self._content_ref, spacing=12, expand=True),
        ]

    def did_mount(self):
        pass

    def load(self):
        content = self._content_ref.current
        if not self._loaded:
            content.controls = [loading_view("Loading dashboard...")]
            content.update()
        try:
            status = self.cli.status()

            row1 = ft.Row([
                status_card("Status", "Connected" if status.online else "Disconnected",
                            icon=ft.Icons.CHECK_CIRCLE if status.online else ft.Icons.CANCEL,
                            status="online" if status.online else "offline"),
                status_card("Device", status.device_name or "N/A", icon=ft.Icons.COMPUTER),
                status_card("Tailscale IPs", status.tailscale_ip[0] if status.tailscale_ip else "N/A",
                            icon=ft.Icons.DNS,
                            subtitle=status.tailscale_ip[1] if len(status.tailscale_ip) > 1 else ""),
                status_card("Version", status.version or "N/A", icon=ft.Icons.BUILD),
            ], spacing=10, expand=True)

            peers_online = sum(1 for p in status.peers if p["online"])
            row2 = ft.Row([
                status_card("Total Peers", str(len(status.peers)), icon=ft.Icons.PEOPLE),
                status_card("Online Peers", str(peers_online), icon=ft.Icons.CHECK_CIRCLE, status="online"),
                status_card("Offline Peers", str(len(status.peers) - peers_online),
                            icon=ft.Icons.CANCEL,
                            status="offline" if peers_online < len(status.peers) else "online"),
                status_card("MagicDNS", "Enabled" if status.magic_dns else "Disabled", icon=ft.Icons.DNS),
            ], spacing=10, expand=True)

            actions = ft.Container(
                content=ft.Column([
                    ft.Text("Quick Actions", size=16, weight=ft.FontWeight.W_600, color=_WHITE),
                    ft.Row([
                        ft.FilledButton("Connect (Up)", icon=ft.Icons.PLAY_ARROW,
                                        on_click=lambda _: self._run_action("up")),
                        ft.FilledButton("Disconnect (Down)", icon=ft.Icons.STOP,
                                        style=ft.ButtonStyle(bgcolor=_RED),
                                        on_click=lambda _: self._run_action("down")),
                        ft.OutlinedButton("Refresh", icon=ft.Icons.REFRESH,
                                          on_click=lambda _: self.load()),
                    ], spacing=8, wrap=True),
                ], spacing=8),
                padding=15,
                border_radius=10,
                bgcolor=_CARD_BG,
                border=ft.Border(left=ft.BorderSide(1, _BORDER), top=ft.BorderSide(1, _BORDER),
                                 right=ft.BorderSide(1, _BORDER), bottom=ft.BorderSide(1, _BORDER)),
            )

            health = ft.Column()
            if status.health:
                health.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Health Warnings", size=16, weight=ft.FontWeight.W_600, color=_WARN),
                            *[ft.Text(f"  \u2022 {h}", size=13, color=_WARN) for h in status.health],
                        ], spacing=4),
                        padding=15,
                        border_radius=10,
                        bgcolor="#3A2A00",
                    )
                )

            row3 = ft.Row(spacing=10, expand=True)
            content.controls = [row1, actions, row2, row3, health]
            content.update()
            self._loaded = True
            self._load_api_stats(row3)
        except TailscaleCLIError as e:
            content.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.WARNING_AMBER, size=48, color=_WARN),
                        ft.Text("Tailscale not available", size=18, weight=ft.FontWeight.BOLD, color=_WHITE),
                        ft.Text(str(e), size=13, color=_GREY, text_align=ft.TextAlign.CENTER),
                        ft.FilledButton("Retry", icon=ft.Icons.REFRESH, on_click=lambda _: self.load()),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    alignment=ft.Alignment.CENTER, expand=True,
                )
            ]
            content.update()

    def _load_api_stats(self, row3: ft.Row):
        def _worker():
            api = self.api
            if not api or not api.authenticated:
                cfg = load_config()
                if not cfg.get("api_key"):
                    return
                api = TailscaleAPIClient(cfg["api_key"], cfg.get("tailnet", ""))

            try:
                keys = api.get_keys()
                users = api.list_users()
                prefs = api.get_dns_preferences()
                magic_dns = prefs.get("magicDNS", prefs.get("magicDns", "?"))

                cards = [
                    status_card("Auth Keys", str(len(keys)), icon=ft.Icons.KEY),
                    status_card("Users", str(len(users)), icon=ft.Icons.PEOPLE),
                    status_card("MagicDNS (API)", "On" if magic_dns is True else "Off",
                                icon=ft.Icons.DNS, status="online" if magic_dns else "offline"),
                ]
                row3.controls = cards
                self.update()
            except TailscaleAPIError:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _run_action(self, action: str):
        try:
            if action == "up":
                self.cli.up()
            elif action == "down":
                self.cli.down()
            self.load()
        except TailscaleCLIError as e:
            page = self.page
            if page:
                page.snack_bar = ft.SnackBar(ft.Text(str(e)), bgcolor=_RED)
                page.snack_bar.open = True
                page.update()
