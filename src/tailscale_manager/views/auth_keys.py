import flet as ft
from ..api_client import TailscaleAPIClient, TailscaleAPIError
from ..config import load as load_config
from ..widgets.loading import loading_view


class AuthKeysView(ft.Container):
    def __init__(self, cli, api=None):
        super().__init__(expand=True)
        self.cli = cli
        self.api = api
        self._loaded = False
        self.list_ref = ft.Ref[ft.Column]()

        self.content = ft.Column(
            [
                ft.Text("Auth Keys", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Manage pre-authentication keys for your tailnet", size=13, color=ft.Colors.GREY_400),
                ft.Divider(height=16),
                ft.Row(
                    [
                        ft.FilledButton("Create Key", icon=ft.Icons.ADD, on_click=lambda _: self._create_dialog()),
                        ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda _: self.load()),
                    ],
                    spacing=8,
                ),
                ft.Divider(height=8),
                ft.Column(ref=self.list_ref, spacing=6, scroll=ft.ScrollMode.AUTO, expand=True),
            ],
            spacing=4,
        )

    def did_mount(self):
        self.load()

    def load(self):
        if not self._loaded:
            self._show_loading()
        api = self.api
        if not api or not api.authenticated:
            cfg = load_config()
            if not cfg.get("api_key"):
                self._show_error("API key not configured — save one in Settings")
                return
            api = TailscaleAPIClient(cfg["api_key"], cfg.get("tailnet", ""))
        try:
            keys = api.get_keys()
            keys.sort(key=lambda k: k.get("created", ""), reverse=True)
            self._loaded = True
            self._render(keys)
        except TailscaleAPIError as e:
            self._show_error(str(e))

    def _show_loading(self):
        self.list_ref.current.controls = [loading_view("Loading keys...")]
        self.list_ref.current.update()

    def _render(self, keys: list):
        if not keys:
            self.list_ref.current.controls = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.KEY, size=64, color=ft.Colors.GREY_600),
                            ft.Text("No auth keys", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("Create one to allow devices to join your tailnet", color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
                    ),
                    alignment=ft.Alignment.CENTER, expand=True,
                )
            ]
            self.list_ref.current.update()
            return

        tiles = []
        for k in keys:
            kid = k.get("id", "")
            key_str = k.get("key", "")
            desc = k.get("description", "") or kid[:12]
            created = (k.get("created", "") or "")[:10]
            expires = (k.get("expires", "") or "")[:10]
            key_preview = key_str[:20] + "..." if len(key_str) > 20 else (key_str or kid[:12])

            tags = k.get("capabilities", {}).get("devices", {}).get("create", {}).get("tags", [])

            tiles.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.KEY, size=22, color=ft.Colors.BLUE_300),
                                width=40,
                            ),
                            ft.Column(
                                [
                                    ft.Text(desc, size=15, weight=ft.FontWeight.W_600),
                                    ft.Text(key_preview, size=11, color=ft.Colors.GREY_500, font_family="monospace"),
                                    ft.Row(
                                        [
                                            ft.Text(f"Created: {created}", size=11, color=ft.Colors.GREY_500),
                                            ft.Text(f"Expires: {expires}", size=11, color=ft.Colors.AMBER_300 if expires else ft.Colors.GREY_500),
                                        ],
                                        spacing=12,
                                    ),
                                    ft.Row(
                                        [ft.Container(content=ft.Text(t, size=9), padding=ft.Padding(left=4, top=1, right=4, bottom=1), border_radius=4, bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.CYAN)) for t in tags],
                                        spacing=4, wrap=True,
                                    ) if tags else ft.Container(),
                                ],
                                spacing=2, expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400, icon_size=18,
                                tooltip="Revoke key", data=kid,
                                on_click=lambda e: self._delete_key(e.control.data),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(left=16, top=12, right=16, bottom=12),
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                    border=ft.Border(top=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), right=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), left=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE))),
                )
            )

        self.list_ref.current.controls = [
            ft.Text(f"{len(keys)} key{'s' if len(keys) != 1 else ''}", size=12, color=ft.Colors.GREY_500),
            *tiles,
        ]
        self.list_ref.current.update()

    def _create_dialog(self):
        desc_ref = ft.Ref[ft.TextField]()
        reusable_ref = ft.Ref[ft.Switch]()
        ephemeral_ref = ft.Ref[ft.Switch]()
        preauthorized_ref = ft.Ref[ft.Switch]()
        tags_ref = ft.Ref[ft.TextField]()

        dlg = ft.AlertDialog(
            title=ft.Text("Create Auth Key"),
            content=ft.Column([
                ft.TextField(ref=desc_ref, label="Description", hint_text="e.g. laptop-2026", width=400),
                ft.TextField(ref=tags_ref, label="Tags (optional, comma-separated)", hint_text="tag:device, tag:prod", width=400),
                ft.Switch(ref=reusable_ref, label="Reusable", value=False),
                ft.Switch(ref=ephemeral_ref, label="Ephemeral", value=True),
                ft.Switch(ref=preauthorized_ref, label="Preauthorized", value=True),
            ], width=420, spacing=8, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton("Create", on_click=lambda _: self._create_key(dlg, desc_ref, reusable_ref, ephemeral_ref, preauthorized_ref, tags_ref)),
            ],
        )
        if self.page:
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()

    def _create_key(self, dlg, desc_ref, reusable_ref, ephemeral_ref, preauthorized_ref, tags_ref):
        api = self.api
        if not api or not api.authenticated:
            cfg = load_config()
            if not cfg.get("api_key"):
                self._snack("API key not configured", ft.Colors.RED_800)
                return
            api = TailscaleAPIClient(cfg["api_key"], cfg.get("tailnet", ""))

        tags = [t.strip() for t in tags_ref.current.value.split(",") if t.strip()] if tags_ref.current.value else []
        capabilities = {
            "devices": {
                "create": {
                    "reusable": reusable_ref.current.value,
                    "ephemeral": ephemeral_ref.current.value,
                    "preauthorized": preauthorized_ref.current.value,
                }
            }
        }
        if tags:
            capabilities["devices"]["create"]["tags"] = tags

        body = {"capabilities": capabilities, "description": desc_ref.current.value or ""}
        try:
            result = api.create_auth_key(**body)
            dlg.open = False
            self.page.update()
            self._snack(f"Key created: {result.get('key', '')}", ft.Colors.GREEN_800)
            self.load()
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _delete_key(self, key_id: str):
        api = self.api
        if not api or not api.authenticated:
            cfg = load_config()
            if not cfg.get("api_key"):
                return
            api = TailscaleAPIClient(cfg["api_key"], cfg.get("tailnet", ""))
        try:
            api.delete_key(key_id)
            self._snack("Key revoked", ft.Colors.GREEN_800)
            self.load()
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _close_dialog(self, dlg: ft.AlertDialog):
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
                        ft.Text("Could not load keys", weight=ft.FontWeight.BOLD),
                        ft.Text(msg, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                        ft.FilledButton("Retry", icon=ft.Icons.REFRESH, on_click=lambda _: self.load()),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
                ),
                alignment=ft.Alignment.CENTER, expand=True,
            )
        ]
        self.list_ref.current.update()
