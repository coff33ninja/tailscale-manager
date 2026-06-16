import flet as ft
from ..api_client import TailscaleAPIClient
from ..config import load as load_config, save as save_config
from ..tailscale_cli import TailscaleCLI, TailscaleCLIError


class SettingsView(ft.Container):
    def __init__(self, cli: TailscaleCLI, api=None):
        super().__init__(expand=True)
        self.cli = cli
        self.api = api

        self.accept_routes = ft.Ref[ft.Switch]()
        self.accept_dns = ft.Ref[ft.Switch]()
        self.ssh = ft.Ref[ft.Switch]()
        self.advertise_routes = ft.Ref[ft.TextField]()
        self.advertise_tags = ft.Ref[ft.TextField]()
        self._api_key_ref = ft.Ref[ft.TextField]()
        self._tailnet_ref = ft.Ref[ft.TextField]()

        self.content = ft.Column(
            [
                ft.Text("Settings", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Configure Tailscale connection options", size=13, color=ft.Colors.GREY_400),
                ft.Divider(height=16),
                ft.Column(
                    [
                        self._api_section(),
                        self._section("Connection", [
                            self._switch_tile("Accept Routes", "Accept subnet routes advertised by other devices",
                                              self.accept_routes),
                            self._switch_tile("Accept DNS", "Use Tailscale DNS settings", self.accept_dns, default=True),
                            self._switch_tile("SSH", "Allow Tailscale SSH connections to this device",
                                              self.ssh, default=True),
                        ]),
                        self._section("Advanced", [
                            self._text_tile("Advertise Routes", "Subnet routes to advertise (e.g. 192.168.1.0/24)",
                                            self.advertise_routes),
                            self._text_tile("Advertise Tags", "Tags to apply to this device (e.g. tag:server)",
                                            self.advertise_tags),
                        ]),
                        self._section("Actions", [
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.FilledButton("Apply & Reconnect", icon=ft.Icons.REFRESH,
                                                        on_click=lambda _: self._apply()),
                                        ft.OutlinedButton("Logout", icon=ft.Icons.LOGOUT,
                                                          on_click=lambda _: self._logout()),
                                        ft.OutlinedButton("Bug Report", icon=ft.Icons.BUG_REPORT,
                                                          on_click=lambda _: self._bug_report()),
                                    ],
                                    spacing=8, wrap=True,
                                ),
                                padding=ft.Padding(top=8),
                            ),
                        ]),
                    ],
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            ],
            spacing=4,
        )

    def did_mount(self):
        self._load_saved_api()

    def _api_section(self) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("API Credentials", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_300),
                    ft.Text("Used for ACLs, device management, DNS, keys, and more", size=11, color=ft.Colors.GREY_500),
                    ft.Row(
                        [
                            ft.TextField(ref=self._api_key_ref, label="Tailscale API Key",
                                         hint_text="tskey-api-xxxxx...", password=True, can_reveal_password=True,
                                         width=400, on_submit=lambda _: self._save_api_creds()),
                            ft.TextField(ref=self._tailnet_ref, label="Tailnet ID",
                                         hint_text="your-tailnet.ts.net", width=300,
                                         on_submit=lambda _: self._save_api_creds()),
                            ft.FilledButton("Save", icon=ft.Icons.SAVE, on_click=lambda _: self._save_api_creds()),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                ],
                spacing=6,
            ),
            padding=15,
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
            border=ft.Border(top=ft.BorderSide(0.5, ft.Colors.with_opacity(0.06, ft.Colors.WHITE)), right=ft.BorderSide(0.5, ft.Colors.with_opacity(0.06, ft.Colors.WHITE)), bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.06, ft.Colors.WHITE)), left=ft.BorderSide(0.5, ft.Colors.with_opacity(0.06, ft.Colors.WHITE))),
        )

    def _save_api_creds(self):
        key = (self._api_key_ref.current.value or "").strip()
        tailnet = (self._tailnet_ref.current.value or "").strip()
        if not key:
            self._snack("API key is required", ft.Colors.RED_800)
            return
        if not tailnet:
            self._snack("Tailnet ID is required", ft.Colors.RED_800)
            return
        save_config(key, tailnet)
        if self.api:
            self.api.reconfigure(key, tailnet)
        else:
            self.api = TailscaleAPIClient(key, tailnet)
        self._snack("API credentials saved", ft.Colors.GREEN_800)

    def _load_saved_api(self):
        cfg = load_config()
        if cfg["api_key"]:
            self._api_key_ref.current.value = cfg["api_key"]
            self._tailnet_ref.current.value = cfg.get("tailnet", "")

    def _section(self, title: str, controls: list) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [ft.Text(title, size=16, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_300)] + controls,
                spacing=6,
            ),
            padding=15,
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
            border=ft.Border(top=ft.BorderSide(0.5, ft.Colors.with_opacity(0.06, ft.Colors.WHITE)), right=ft.BorderSide(0.5, ft.Colors.with_opacity(0.06, ft.Colors.WHITE)), bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.06, ft.Colors.WHITE)), left=ft.BorderSide(0.5, ft.Colors.with_opacity(0.06, ft.Colors.WHITE))),
        )

    def _switch_tile(self, title: str, subtitle: str, ref: ft.Ref, default: bool = False) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column([ft.Text(title, size=14), ft.Text(subtitle, size=11, color=ft.Colors.GREY_500)], spacing=1, expand=True),
                    ft.Switch(ref=ref, value=default),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=0, top=4, right=0, bottom=4),
        )

    def _text_tile(self, title: str, hint: str, ref: ft.Ref) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=14),
                    ft.TextField(ref=ref, hint_text=hint, border_radius=8, height=44),
                ],
                spacing=4,
            ),
            padding=ft.Padding(left=0, top=4, right=0, bottom=4),
        )

    def _apply(self):
        try:
            self.cli.up(
                accept_routes=self.accept_routes.current.value,
                accept_dns=self.accept_dns.current.value,
                ssh=self.ssh.current.value,
                advertise_routes=self.advertise_routes.current.value or "",
                advertise_tags=self.advertise_tags.current.value or "",
            )
            self._snack("Settings applied and reconnected", ft.Colors.GREEN_800)
        except TailscaleCLIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _logout(self):
        try:
            self.cli.logout()
            self._snack("Logged out of Tailscale", ft.Colors.GREEN_800)
        except TailscaleCLIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _bug_report(self):
        try:
            report = self.cli.bug_report()
            self._snack("Bug report generated (check terminal)", ft.Colors.GREEN_800)
        except TailscaleCLIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _snack(self, msg: str, color: str):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
            self.page.snack_bar.open = True
            self.page.update()
