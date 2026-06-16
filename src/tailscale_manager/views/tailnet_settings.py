import json

import flet as ft
from ..api_client import TailscaleAPIClient, TailscaleAPIError
from ..config import load as load_config


class TailnetSettingsView(ft.Container):
    def __init__(self, cli, api=None):
        super().__init__(expand=True)
        self.cli = cli
        self.api = api
        self.editor_ref = ft.Ref[ft.TextField]()
        self._current_settings = {}
        self._modified = False

        self.content = ft.Column(
            [
                ft.Text("Tailnet Settings", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("View and modify tailnet-level settings", size=13, color=ft.Colors.GREY_400),
                ft.Divider(height=16),
                ft.Row([
                    ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda _: self.load(), tooltip="Refresh"),
                    ft.FilledButton("Save Settings", icon=ft.Icons.SAVE, on_click=lambda _: self._save()),
                ], spacing=8),
                ft.TextField(
                    ref=self.editor_ref,
                    multiline=True,
                    min_lines=20,
                    max_lines=40,
                    border_radius=8,
                    border_color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                    text_style=ft.TextStyle(size=12, font_family="monospace"),
                    expand=True,
                    on_change=lambda _: self._mark_modified(),
                    hint_text="Loading settings...",
                ),
                ft.Text("Edit as JSON. Changes are applied directly.", size=11, color=ft.Colors.GREY_500),
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
        api = self._get_api()
        if not api:
            self.editor_ref.current.value = "# API not configured\n# Go to Settings to add API credentials"
            self.editor_ref.current.update()
            return
        try:
            settings = api.get_tailnet_settings()
            self._current_settings = settings
            formatted = json.dumps(settings, indent=2, ensure_ascii=False)
            self.editor_ref.current.value = formatted
            self.editor_ref.current.hint_text = ""
            self._modified = False
            self.editor_ref.current.update()
        except TailscaleAPIError as e:
            self.editor_ref.current.value = f"# Error: {e}"
            self.editor_ref.current.update()

    def _mark_modified(self):
        self._modified = True

    def _save(self):
        raw = (self.editor_ref.current.value or "").strip()
        if not raw:
            self._snack("Empty settings", ft.Colors.RED_800)
            return
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            self._snack(f"Invalid JSON: {e}", ft.Colors.RED_800)
            return

        api = self._get_api()
        if not api:
            return
        try:
            result = api.update_tailnet_settings(parsed)
            self._current_settings = result
            self.editor_ref.current.value = json.dumps(result, indent=2, ensure_ascii=False)
            self._modified = False
            self.editor_ref.current.update()
            self._snack("Settings saved", ft.Colors.GREEN_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _snack(self, msg: str, color: str):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msg, size=13), bgcolor=color)
            self.page.snack_bar.open = True
            self.page.update()
