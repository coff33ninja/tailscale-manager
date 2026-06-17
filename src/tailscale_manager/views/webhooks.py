import flet as ft
from ..api_client import TailscaleAPIClient, TailscaleAPIError
from ..config import load as load_config


class WebhooksView(ft.Container):
    def __init__(self, cli, api=None):
        super().__init__(expand=True)
        self.cli = cli
        self.api = api
        self.list_ref = ft.Ref[ft.Column]()

        self.content = ft.Column(
            [
                ft.Text("Webhooks", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Manage HTTP webhook endpoints for tailnet events", size=13, color=ft.Colors.GREY_400),
                ft.Divider(height=16),
                ft.Row(
                    [
                        ft.FilledButton("Create Webhook", icon=ft.Icons.ADD, on_click=lambda _: self._create_dialog()),
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
        self._show_loading()
        api = self._get_api()
        if not api:
            self._show_error("API not configured")
            return
        try:
            hooks = api.list_webhooks()
            self._render(hooks, api)
        except TailscaleAPIError as e:
            self._show_error(str(e))

    def _get_api(self):
        if self.api and self.api.authenticated:
            return self.api
        cfg = load_config()
        if cfg.get("api_key"):
            return TailscaleAPIClient(cfg["api_key"], cfg.get("tailnet", ""))
        return None

    def _show_loading(self):
        self.list_ref.current.controls = [
            ft.Container(
                content=ft.Column(
                    [ft.ProgressRing(width=32, height=32), ft.Text("Loading webhooks...", color=ft.Colors.GREY_500, size=14)],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12,
                ),
                alignment=ft.Alignment.CENTER, expand=True,
            )
        ]
        self.list_ref.current.update()

    def _render(self, hooks: list, api):
        if not hooks:
            self.list_ref.current.controls = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.WEBHOOK, size=64, color=ft.Colors.GREY_600),
                            ft.Text("No webhooks configured", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("Create one to receive Tailscale events via HTTP", color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
                    ),
                    alignment=ft.Alignment.CENTER, expand=True,
                )
            ]
            self.list_ref.current.update()
            return

        tiles = []
        for h in hooks:
            eid = h.get("endpointId", "")
            url = h.get("url", "")
            provider = h.get("providerType", "none") or "custom"
            subs = h.get("subscriptions", [])
            last_req = (h.get("lastRequestAt", "") or "")[:19]

            tiles.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.WEBHOOK, size=22, color=ft.Colors.BLUE_300),
                            width=40,
                        ),
                        ft.Column([
                            ft.Text(url or "(no URL)", size=14, weight=ft.FontWeight.W_600),
                            ft.Row([
                                ft.Container(content=ft.Text(provider, size=9),
                                             padding=ft.Padding(left=4, top=1, right=4, bottom=1),
                                             border_radius=4, bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.PURPLE)),
                                *[ft.Container(content=ft.Text(s, size=9),
                                               padding=ft.Padding(left=4, top=1, right=4, bottom=1),
                                               border_radius=4, bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.CYAN)) for s in subs[:3]],
                            ], spacing=4, wrap=True),
                            ft.Text(f"Last request: {last_req}", size=10, color=ft.Colors.GREY_500) if last_req else ft.Container(),
                        ], spacing=2, expand=True),
                        ft.Row([
                            ft.IconButton(icon=ft.Icons.PLAY_ARROW, icon_size=16, height=28, width=28,
                                          tooltip="Test", data=eid,
                                          on_click=lambda e: self._test(e.control.data, api)),
                            ft.IconButton(icon=ft.Icons.REFRESH, icon_size=16, height=28, width=28,
                                          tooltip="Rotate secret", data=eid,
                                          on_click=lambda e: self._rotate(e.control.data, api)),
                            ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400, icon_size=16,
                                          height=28, width=28, tooltip="Delete", data=eid,
                                          on_click=lambda e: self._delete(e.control.data, api)),
                        ], spacing=4),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(left=16, top=12, right=8, bottom=12),
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                    border=ft.Border(top=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), right=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), left=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE))),
                )
            )

        self.list_ref.current.controls = [
            ft.Text(f"{len(hooks)} webhook{'s' if len(hooks)!=1 else ''}", size=12, color=ft.Colors.GREY_500),
            *tiles,
        ]
        self.list_ref.current.update()

    def _create_dialog(self):
        url_ref = ft.Ref[ft.TextField]()
        subs_ref = ft.Ref[ft.TextField]()
        dlg = ft.AlertDialog(
            title=ft.Text("Create Webhook"),
            content=ft.Column([
                ft.TextField(ref=url_ref, label="Endpoint URL", hint_text="https://example.com/webhook", width=400),
                ft.TextField(ref=subs_ref, label="Event types (comma-separated)",
                             hint_text="nodeCreated, nodeDeleted, policyPush", width=400),
            ], width=420, spacing=8),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton("Create", on_click=lambda _: self._create(url_ref, subs_ref, dlg)),
            ],
        )
        if self.page:
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()

    def _create(self, url_ref, subs_ref, dlg):
        url = (url_ref.current.value or "").strip()
        if not url:
            self._snack("URL is required", ft.Colors.RED_800)
            return
        api = self._get_api()
        if not api:
            return
        raw = (subs_ref.current.value or "").strip()
        subs = [s.strip() for s in raw.split(",") if s.strip()]
        try:
            api.create_webhook({"url": url, "subscriptions": subs})
            dlg.open = False
            self.page.update()
            self._snack("Webhook created", ft.Colors.GREEN_800)
            self.load()
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _test(self, eid: str, api):
        try:
            api.test_webhook(eid)
            self._snack("Test event sent", ft.Colors.GREEN_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _rotate(self, eid: str, api):
        try:
            api.rotate_webhook_secret(eid)
            self._snack("Secret rotated", ft.Colors.GREEN_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _delete(self, eid: str, api):
        try:
            api.delete_webhook(eid)
            self._snack("Webhook deleted", ft.Colors.GREEN_800)
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
                        ft.Text("Could not load webhooks", weight=ft.FontWeight.BOLD),
                        ft.Text(msg, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                        ft.FilledButton("Retry", icon=ft.Icons.REFRESH, on_click=lambda _: self.load()),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
                ),
                alignment=ft.Alignment.CENTER, expand=True,
            )
        ]
        self.list_ref.current.update()
