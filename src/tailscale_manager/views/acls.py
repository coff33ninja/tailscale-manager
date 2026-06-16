import json

import flet as ft

from ..api_client import TailscaleAPIClient, TailscaleAPIError
from ..config import load as load_config, save as save_config
from ..tailscale_cli import TailscaleCLI


class ACLsView(ft.Container):
    def __init__(self, cli: TailscaleCLI, api=None):
        super().__init__(expand=True)
        self.cli = cli
        self._api: TailscaleAPIClient | None = api
        self._etag = ""

        self.editor_ref = ft.Ref[ft.TextField]()
        self.status_ref = ft.Ref[ft.Container]()
        self.api_key_ref = ft.Ref[ft.TextField]()
        self.tailnet_ref = ft.Ref[ft.TextField]()
        self.save_btn = ft.Ref[ft.FilledButton]()
        self.validate_btn = ft.Ref[ft.OutlinedButton]()

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
                self._build_api_key_section(),
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
                        ft.FilledButton("Save ACL", ref=self.save_btn, icon=ft.Icons.SAVE, on_click=lambda _: self._save_acl()),
                        ft.OutlinedButton("Validate", ref=self.validate_btn, icon=ft.Icons.CHECK, on_click=lambda _: self._validate_acl()),
                        ft.Container(expand=True),
                    ],
                    spacing=8,
                ),
            ],
            spacing=4,
        )
        self._loaded = False

    def _build_api_key_section(self) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("API Credentials", size=14, weight=ft.FontWeight.W_600),
                    ft.Row(
                        [
                            ft.TextField(
                                ref=self.api_key_ref,
                                label="Tailscale API Key",
                                hint_text="tskey-api-xxxxx...",
                                password=True,
                                can_reveal_password=True,
                                width=400,
                                on_submit=lambda _: self._save_creds(),
                            ),
                            ft.TextField(
                                ref=self.tailnet_ref,
                                label="Tailnet ID",
                                hint_text="your-tailnet.ts.net",
                                width=300,
                                on_submit=lambda _: self._save_creds(),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SAVE,
                                tooltip="Save credentials",
                                on_click=lambda _: self._save_creds(),
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Container(height=4),
                    ft.Text(
                        "Get a key at https://login.tailscale.com/admin/settings/keys (read/write access required)",
                        size=11, color=ft.Colors.GREY_500,
                    ),
                ],
                spacing=6,
            ),
            padding=15,
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
        )

    def did_mount(self):
        if not self._loaded:
            self._load_saved_config()
            self._loaded = True

    def _load_saved_config(self):
        cfg = load_config()
        self.api_key_ref.current.value = cfg["api_key"]
        self.tailnet_ref.current.value = cfg.get("tailnet", "")
        self.update()
        if self._api and self._api.authenticated:
            self._fetch_acl()
        else:
            self._show_idle()

    def _save_creds(self):
        key = (self.api_key_ref.current.value or "").strip()
        tailnet = (self.tailnet_ref.current.value or "").strip()
        if not key:
            self._snack("API key is required", ft.Colors.RED_800)
            return
        if not tailnet:
            self._snack("Tailnet ID is required", ft.Colors.RED_800)
            return
        save_config(key, tailnet)
        self._init_api(key, tailnet)
        self._snack("Credentials saved", ft.Colors.GREEN_800)

    def _init_api(self, api_key: str, tailnet: str):
        if not api_key.startswith("tskey-"):
            self._snack("Invalid API key format (must start with tskey-)", ft.Colors.RED_800)
            return
        if self._api:
            self._api.reconfigure(api_key, tailnet)
        else:
            self._api = TailscaleAPIClient(api_key, tailnet)

    def _fetch_acl(self):
        if not self._api or not self._api.authenticated:
            self._snack("Save a valid API key first", ft.Colors.AMBER_800)
            return
        try:
            data = self._api.get_acl()
            self._etag = data.pop("etag", "")
            pretty = json.dumps(data, indent=2)
            self.editor_ref.current.value = pretty
            self.editor_ref.current.update()
            self._snack("ACL fetched successfully", ft.Colors.GREEN_800)
            self._show_idle()
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _save_acl(self):
        if not self._api or not self._api.authenticated:
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
            self._api.set_acl(acl, self._etag)
            self._snack("ACL saved successfully", ft.Colors.GREEN_800)
            self._fetch_acl()
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _validate_acl(self):
        if not self._api or not self._api.authenticated:
            return
        raw = self.editor_ref.current.value.strip()
        if not raw:
            return
        try:
            acl = json.loads(raw)
            warnings = self._api.validate_acl(acl)
            if warnings:
                msg = "\n".join(f"  \u2022 {w}" for w in warnings)
                self._snack(f"Warnings:\n{msg}", ft.Colors.AMBER_800)
            else:
                self._snack("ACL is valid — no warnings", ft.Colors.GREEN_800)
        except json.JSONDecodeError as e:
            self._snack(f"Invalid JSON: {e}", ft.Colors.RED_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _show_idle(self):
        if self.status_ref.current:
            self.status_ref.current.content = None
            self.status_ref.current.update()

    def _snack(self, msg: str, color: str):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msg, size=13), bgcolor=color)
            self.page.snack_bar.open = True
            self.page.update()
