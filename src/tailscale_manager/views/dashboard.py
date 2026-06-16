import flet as ft
from ..tailscale_cli import TailscaleCLI, TailscaleCLIError


_RED = "#FF5252"
_WHITE = "#FFFFFF"
_GREY = "#9E9E9E"
_GREY_LIGHT = "#BDBDBD"
_CARD_BG = "#2A2A3E"
_BORDER = "#3A3A5E"
_WARN = "#FFB74D"


class DashboardView(ft.Column):
    def __init__(self, cli: TailscaleCLI):
        super().__init__(expand=True, spacing=12)
        self.cli = cli

    def did_mount(self):
        pass

    def load(self):
        self.controls = [
            ft.Text("Dashboard", size=28, weight=ft.FontWeight.BOLD, color=_WHITE),
            ft.Text("Loading...", size=13, color=_GREY),
        ]
        self.update()
        try:
            status = self.cli.status()

            def _card(title, value, subtitle=""):
                return ft.Container(
                    content=ft.Column([
                        ft.Text(title, size=12, color=_GREY),
                        ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=_WHITE),
                        ft.Text(subtitle, size=11, color=_GREY_LIGHT, visible=bool(subtitle)),
                    ], spacing=2, expand=True),
                    padding=16,
                    border_radius=10,
                    bgcolor=_CARD_BG,
                    border=ft.Border(left=ft.BorderSide(1, _BORDER), top=ft.BorderSide(1, _BORDER), right=ft.BorderSide(1, _BORDER), bottom=ft.BorderSide(1, _BORDER)),
                    expand=True,
                )

            row1 = ft.Row([
                _card("Status", "Connected" if status.online else "Disconnected"),
                _card("Device", status.device_name or "N/A"),
                _card("IP", status.tailscale_ip[0] if status.tailscale_ip else "N/A",
                      status.tailscale_ip[1] if len(status.tailscale_ip) > 1 else ""),
                _card("Version", status.version or "N/A"),
            ], spacing=10, expand=True)

            peers_online = sum(1 for p in status.peers if p["online"])
            row2 = ft.Row([
                _card("Total Peers", str(len(status.peers))),
                _card("Online", str(peers_online)),
                _card("Offline", str(len(status.peers) - peers_online)),
                _card("MagicDNS", "Enabled" if status.magic_dns else "Disabled"),
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
                border=ft.Border(left=ft.BorderSide(1, _BORDER), top=ft.BorderSide(1, _BORDER), right=ft.BorderSide(1, _BORDER), bottom=ft.BorderSide(1, _BORDER)),
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

            self.controls = [
                ft.Text("Dashboard", size=28, weight=ft.FontWeight.BOLD, color=_WHITE),
                ft.Text("Tailscale connection overview", size=13, color=_GREY),
                ft.Divider(height=20, color=_BORDER),
                row1, actions, row2, health,
            ]
            self.update()
        except TailscaleCLIError as e:
            self.controls = [
                ft.Text("Dashboard", size=28, weight=ft.FontWeight.BOLD, color=_WHITE),
                ft.Text("Tailscale connection overview", size=13, color=_GREY),
                ft.Divider(height=20, color=_BORDER),
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
            self.update()

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
