import datetime
import json

import flet as ft
from ..api_client import TailscaleAPIClient, TailscaleAPIError
from ..config import load as load_config


class AuditLogsView(ft.Container):
    def __init__(self, cli, api=None):
        super().__init__(expand=True)
        self.cli = cli
        self.api = api
        self.log_ref = ft.Ref[ft.Column]()

        now = datetime.datetime.utcnow().isoformat()[:19] + "Z"
        yesterday = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat()[:19] + "Z"

        self.start_ref = ft.Ref[ft.TextField]()
        self.end_ref = ft.Ref[ft.TextField]()

        self.content = ft.Column(
            [
                ft.Text("Audit Logs", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("View configuration changes and network activity", size=13, color=ft.Colors.GREY_400),
                ft.Divider(height=16),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Date Range", size=14, weight=ft.FontWeight.W_600),
                        ft.Row([
                            ft.TextField(ref=self.start_ref, label="Start (ISO)", hint_text="2026-01-01T00:00:00Z",
                                         value=yesterday, width=300, height=44),
                            ft.TextField(ref=self.end_ref, label="End (ISO)", hint_text="2026-01-02T00:00:00Z",
                                         value=now, width=300, height=44),
                            ft.FilledButton("Search", icon=ft.Icons.SEARCH, on_click=lambda _: self._search()),
                        ], spacing=8, wrap=True),
                    ], spacing=6),
                    padding=15, border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                ),
                ft.Divider(height=8),
                ft.Column(ref=self.log_ref, spacing=4, scroll=ft.ScrollMode.AUTO, expand=True),
            ],
            spacing=4,
        )

    def did_mount(self):
        pass

    def _get_api(self):
        if self.api and self.api.authenticated:
            return self.api
        cfg = load_config()
        if cfg.get("api_key"):
            return TailscaleAPIClient(cfg["api_key"], cfg.get("tailnet", ""))
        return None

    def _search(self):
        start = (self.start_ref.current.value or "").strip()
        end = (self.end_ref.current.value or "").strip()
        if not start or not end:
            self._snack("Start and end dates required", ft.Colors.RED_800)
            return

        api = self._get_api()
        if not api:
            self._snack("API not configured", ft.Colors.RED_800)
            return

        self.log_ref.current.controls = [
            ft.Container(
                content=ft.ProgressRing(width=24, height=24),
                alignment=ft.Alignment.CENTER, expand=True,
            )
        ]
        self.log_ref.current.update()

        try:
            result = api.list_configuration_audit_logs(start, end)
            self._render(result)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)
            self.log_ref.current.controls = [ft.Text(f"Error: {e}", color=ft.Colors.RED_400)]
            self.log_ref.current.update()

    def _render(self, result: dict):
        events = result if isinstance(result, list) else result.get("events", result.get("logs", [result]))
        if not events:
            self.log_ref.current.controls = [ft.Text("No audit log entries found", color=ft.Colors.GREY_500)]
            self.log_ref.current.update()
            return

        entries = []
        for ev in events[:100]:
            ts = (ev.get("timestamp", ev.get("time", ev.get("created", ""))) or "")[:19]
            actor = ev.get("actor", ev.get("user", ev.get("loginName", "")))
            action = ev.get("action", ev.get("event", ev.get("type", "")))
            target = ev.get("target", ev.get("object", ""))

            entries.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(ts, size=11, color=ft.Colors.GREY_500, font_family="monospace"),
                            ft.Text(str(action), size=13, weight=ft.FontWeight.W_600),
                            ft.Row([
                                ft.Text(f"Actor: {actor}", size=11, color=ft.Colors.GREY_500),
                                ft.Text(f"Target: {target}", size=11, color=ft.Colors.GREY_500) if target else ft.Container(),
                            ], spacing=8),
                        ], spacing=2, expand=True),
                    ], vertical_alignment=ft.CrossAxisAlignment.START),
                    padding=ft.Padding(left=16, top=8, right=16, bottom=8),
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
                )
            )

        self.log_ref.current.controls = [
            ft.Text(f"{len(events)} event{'s' if len(events)!=1 else ''} (showing first 100)", size=12, color=ft.Colors.GREY_500),
            *entries,
        ]
        self.log_ref.current.update()

    def _snack(self, msg: str, color: str):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msg, size=13), bgcolor=color)
            self.page.snack_bar.open = True
            self.page.update()
