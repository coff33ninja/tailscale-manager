import json

import flet as ft

from ..api_client import TailscaleAPIError
from ..config import load as load_config
from ..tailscale_cli import TailscaleCLI


class ACLsView(ft.Container):
    def __init__(self, cli: TailscaleCLI, api=None):
        super().__init__(expand=True)
        self.cli = cli
        self.api = api
        self._etag = ""

        self.editor_ref = ft.Ref[ft.TextField]()
        self.status_ref = ft.Ref[ft.Container]()

        self.content = ft.Column(
            [
                ft.Text("ACLs", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Manage Tailscale ACL policies via the API (requires an API key)",
                    size=13, color=ft.Colors.GREY_400,
                ),
                ft.Divider(height=16),
                ft.Container(ref=self.status_ref),
                ft.Divider(height=8),
                ft.Text("ACL Policy (HuJSON)", size=14, weight=ft.FontWeight.W_600),
                ft.TextField(
                    ref=self.editor_ref,
                    multiline=True,
                    min_lines=12,
                    max_lines=20,
                    hint_text="Paste ACL JSON here...",
                    border_radius=8,
                    expand=True,
                ),
                ft.Row(
                    [
                        ft.FilledButton("Fetch ACL", icon=ft.Icons.DOWNLOAD, on_click=lambda _: self._fetch_acl()),
                        ft.FilledButton("Save ACL", icon=ft.Icons.SAVE, on_click=lambda _: self._save_acl()),
                        ft.OutlinedButton("Validate", icon=ft.Icons.CHECK, on_click=lambda _: self._validate_acl()),
                        ft.Container(expand=True),
                    ],
                    spacing=8,
                ),
            ],
            spacing=4,
        )

    def _get_api(self):
        if self.api and self.api.authenticated:
            return self.api
        cfg = load_config()
        if cfg.get("api_key"):
            from ..api_client import TailscaleAPIClient
            return TailscaleAPIClient(cfg["api_key"], cfg.get("tailnet", ""))
        return None

    def did_mount(self):
        self._fetch_acl()

    def _fetch_acl(self):
        api = self._get_api()
        if not api:
            self._snack("Configure an API key in Settings first", ft.Colors.AMBER_800)
            return
        try:
            data = api.get_acl()
            self._etag = data.pop("etag", "")
            pretty = json.dumps(data, indent=2)
            self.editor_ref.current.value = pretty
            self.editor_ref.current.update()
            self._snack("ACL fetched successfully", ft.Colors.GREEN_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _save_acl(self):
        api = self._get_api()
        if not api:
            return
        raw = self.editor_ref.current.value.strip()
        if not raw:
            self._snack("Editor is empty", ft.Colors.AMBER_800)
            return
        try:
            acl = json.loads(raw)
        except json.JSONDecodeError as e:
            self._snack(f"Invalid JSON: {e}", ft.Colors.RED_800)
            return
        try:
            warnings = api.validate_acl(acl)
            if warnings:
                msg = "\n".join(f"  \u2022 {w}" for w in warnings[:5])
                self._snack(f"Validation warnings:\n{msg}", ft.Colors.AMBER_800)
            api.set_acl(acl, self._etag)
            self._snack("ACL saved successfully", ft.Colors.GREEN_800)
            self._fetch_acl()
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _validate_acl(self):
        api = self._get_api()
        if not api:
            return
        raw = self.editor_ref.current.value.strip()
        if not raw:
            return
        try:
            acl = json.loads(raw)
            warnings = api.validate_acl(acl)
            if warnings:
                msg = "\n".join(f"  \u2022 {w}" for w in warnings)
                self._snack(f"Warnings:\n{msg}", ft.Colors.AMBER_800)
            else:
                self._snack("ACL is valid — no warnings", ft.Colors.GREEN_800)
        except json.JSONDecodeError as e:
            self._snack(f"Invalid JSON: {e}", ft.Colors.RED_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _snack(self, msg: str, color: str):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msg, size=13), bgcolor=color)
            self.page.snack_bar.open = True
            self.page.update()
