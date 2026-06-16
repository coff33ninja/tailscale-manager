import flet as ft
from ..api_client import TailscaleAPIClient, TailscaleAPIError
from ..config import load as load_config


class DevicePostureView(ft.Container):
    def __init__(self, cli, api=None):
        super().__init__(expand=True)
        self.cli = cli
        self.api = api
        self.list_ref = ft.Ref[ft.Column]()

        self.content = ft.Column(
            [
                ft.Text("Device Posture", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Manage device posture integrations and attribute retrieval",
                        size=13, color=ft.Colors.GREY_400),
                ft.Divider(height=16),
                ft.Row([
                    ft.FilledButton("Add Integration", icon=ft.Icons.ADD, on_click=lambda _: self._create_dialog()),
                    ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda _: self.load()),
                ], spacing=8),
                ft.Column(ref=self.list_ref, spacing=6, scroll=ft.ScrollMode.AUTO, expand=True),
            ],
            spacing=4,
        )

    def did_mount(self):
        self.load()

    def _get_api(self):
        if self.api and self.api.authenticated:
            return self.api
        cfg = load_config()
        if cfg.get("api_key"):
            return TailscaleAPIClient(cfg["api_key"], cfg.get("tailnet", ""))
        return None

    def load(self):
        self._show_loading()
        api = self._get_api()
        if not api:
            self._show_error("API not configured")
            return
        try:
            integrations = api.list_posture_integrations()
            self._render(integrations, api)
        except TailscaleAPIError as e:
            self._show_error(str(e))

    def _show_loading(self):
        self.list_ref.current.controls = [
            ft.Container(
                content=ft.Column(
                    [ft.ProgressRing(width=32, height=32),
                     ft.Text("Loading posture integrations...", color=ft.Colors.GREY_500, size=14)],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12,
                ),
                alignment=ft.Alignment.CENTER, expand=True,
            )
        ]
        self.list_ref.current.update()

    def _render(self, integrations: list, api):
        if not integrations:
            self.list_ref.current.controls = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.SECURITY, size=64, color=ft.Colors.GREY_600),
                            ft.Text("No posture integrations", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("Add an MDM or device compliance provider to get started",
                                    color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
                    ),
                    alignment=ft.Alignment.CENTER, expand=True,
                )
            ]
            self.list_ref.current.update()
            return

        tiles = []
        for integ in integrations:
            pid = integ.get("id", integ.get("integrationId", ""))
            name = integ.get("displayName", integ.get("name", "(unnamed)"))
            provider = integ.get("provider", integ.get("providerType", "unknown"))
            itype = integ.get("type", integ.get("integrationType", ""))
            cols = integ.get("collectionType", integ.get("collection", ""))

            tiles.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.SECURITY, size=22, color=ft.Colors.GREEN_300),
                            width=40,
                        ),
                        ft.Column([
                            ft.Text(name, size=14, weight=ft.FontWeight.W_600),
                            ft.Row([
                                ft.Container(content=ft.Text(provider, size=9),
                                             padding=ft.Padding(left=4, top=1, right=4, bottom=1),
                                             border_radius=4, bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.BLUE)),
                                ft.Container(content=ft.Text(cols, size=9) if cols else ft.Container(),
                                             padding=ft.Padding(left=4, top=1, right=4, bottom=1),
                                             border_radius=4, bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.PURPLE)),
                            ], spacing=4, wrap=True),
                            ft. Text(f"ID: {pid}", size=10, color=ft.Colors.GREY_500, font_family="monospace"),
                        ], spacing=2, expand=True),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400,
                                      icon_size=16, height=28, width=28, tooltip="Delete",
                                      data=pid,
                                      on_click=lambda e: self._delete(e.control.data, api)),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(left=16, top=12, right=8, bottom=12),
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                    border=ft.Border(top=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), right=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), left=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE))),
                )
            )

        self.list_ref.current.controls = [
            ft.Text(f"{len(integrations)} integration{'s' if len(integrations)!=1 else ''}",
                    size=12, color=ft.Colors.GREY_500),
            *tiles,
        ]
        self.list_ref.current.update()

    def _create_dialog(self):
        name_ref = ft.Ref[ft.TextField]()
        provider_ref = ft.Ref[ft.TextField]()
        dlg = ft.AlertDialog(
            title=ft.Text("Add Posture Integration"),
            content=ft.Column([
                ft.TextField(ref=name_ref, label="Display Name", hint_text="My MDM", width=400),
                ft.TextField(ref=provider_ref, label="Provider Type",
                             hint_text="jamf, kandji, intune, crowdstrike, sentinelone", width=400),
            ], width=420, spacing=8),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton("Create", on_click=lambda _: self._create(name_ref, provider_ref, dlg)),
            ],
        )
        if self.page:
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()

    def _create(self, name_ref, provider_ref, dlg):
        name = (name_ref.current.value or "").strip()
        provider = (provider_ref.current.value or "").strip()
        if not name or not provider:
            self._snack("Name and provider are required", ft.Colors.RED_800)
            return
        api = self._get_api()
        if not api:
            return
        try:
            api.create_posture_integration({"displayName": name, "providerType": provider})
            dlg.open = False
            self.page.update()
            self._snack("Integration created", ft.Colors.GREEN_800)
            self.load()
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _delete(self, pid: str, api):
        try:
            api.delete_posture_integration(pid)
            self._snack("Integration deleted", ft.Colors.GREEN_800)
            self.load()
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _close_dialog(self, dlg):
        dlg.open = False
        if self.page:
            self.page.update()

    def _snack(self, msg: str, color: str):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msg, size=13), bgcolor=color)
            self.page.snack_bar.open = True
            self.page.update()

    def _show_error(self, msg: str):
        self.list_ref.current.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=ft.Colors.RED_400),
                        ft.Text("Could not load integrations", weight=ft.FontWeight.BOLD),
                        ft.Text(msg, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                        ft.FilledButton("Retry", icon=ft.Icons.REFRESH, on_click=lambda _: self.load()),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
                ),
                alignment=ft.Alignment.CENTER, expand=True,
            )
        ]
        self.list_ref.current.update()
