import flet as ft
from ..api_client import TailscaleAPIClient, TailscaleAPIError
from ..config import load as load_config
from ..widgets.loading import loading_view


class UsersView(ft.Container):
    def __init__(self, cli, api=None):
        super().__init__(expand=True)
        self.cli = cli
        self.api = api
        self._loaded = False
        self.list_ref = ft.Ref[ft.Column]()

        self.content = ft.Column(
            [
                ft.Text("Users", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Manage users in your tailnet", size=13, color=ft.Colors.GREY_400),
                ft.Divider(height=16),
                ft.Row(
                    [
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
        api = self._get_api()
        if not api:
            self._show_error("API not configured")
            return
        try:
            users = api.list_users()
            users.sort(key=lambda u: u.get("displayName", "").lower())
            self._loaded = True
            self._render(users, api)
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
        self.list_ref.current.controls = [loading_view("Loading users...")]
        self.list_ref.current.update()

    def _render(self, users: list, api):
        if not users:
            self.list_ref.current.controls = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=64, color=ft.Colors.GREY_600),
                            ft.Text("No users found", size=16, weight=ft.FontWeight.BOLD),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
                    ),
                    alignment=ft.Alignment.CENTER, expand=True,
                )
            ]
            self.list_ref.current.update()
            return

        tiles = []
        for u in users:
            uid = u.get("id", "")
            name = u.get("displayName", "Unknown")
            login = u.get("loginName", "")
            role = u.get("role", "")
            status = u.get("status", "")
            devices = u.get("deviceCount", 0)
            created = (u.get("created", "") or "")[:10]

            role_colors = {"owner": ft.Colors.AMBER_400, "admin": ft.Colors.BLUE_300, "member": ft.Colors.GREEN_300, "it-admin": ft.Colors.PURPLE_300}
            role_color = role_colors.get(role, ft.Colors.GREY_500)
            status_color = ft.Colors.GREEN_400 if status == "active" else (ft.Colors.RED_400 if status == "suspended" else ft.Colors.GREY_500)

            actions = ft.Row(spacing=4)
            if role != "owner" and status != "suspended":
                actions.controls.append(
                    ft.IconButton(icon=ft.Icons.BLOCK, icon_size=16, height=28, width=28,
                                  tooltip="Suspend", data=uid,
                                  on_click=lambda e: self._suspend(e.control.data, api)),
                )
            if status == "suspended":
                actions.controls.append(
                    ft.IconButton(icon=ft.Icons.RESTORE, icon_size=16, height=28, width=28,
                                  tooltip="Restore", data=uid,
                                  on_click=lambda e: self._restore(e.control.data, api)),
                )

            tiles.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(name[:2].upper(), size=16, color=ft.Colors.WHITE),
                            width=40, height=40, border_radius=20,
                            bgcolor=ft.Colors.with_opacity(0.2, role_color),
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column([
                            ft.Text(name, size=15, weight=ft.FontWeight.W_600),
                            ft.Row([
                                ft.Text(login, size=11, color=ft.Colors.GREY_500),
                                ft.Text(f"\u00b7 {devices} device{'s' if devices!=1 else ''}", size=11, color=ft.Colors.GREY_500),
                            ], spacing=4),
                            ft.Row([
                                ft.Container(content=ft.Text(role, size=9, color=role_color),
                                             padding=ft.Padding(left=4, top=1, right=4, bottom=1),
                                             border_radius=4, bgcolor=ft.Colors.with_opacity(0.12, role_color)),
                                ft.Container(content=ft.Text(status, size=9, color=status_color),
                                             padding=ft.Padding(left=4, top=1, right=4, bottom=1),
                                             border_radius=4, bgcolor=ft.Colors.with_opacity(0.12, status_color)),
                                ft.Text(f"Created: {created}", size=10, color=ft.Colors.GREY_500),
                            ], spacing=4),
                        ], spacing=2, expand=True),
                        actions,
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(left=16, top=12, right=16, bottom=12),
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                    border=ft.Border(top=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), right=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), left=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE))),
                )
            )

        self.list_ref.current.controls = [
            ft.Text(f"{len(users)} user{'s' if len(users) != 1 else ''}", size=12, color=ft.Colors.GREY_500),
            *tiles,
        ]
        self.list_ref.current.update()

    def _suspend(self, uid: str, api):
        try:
            api.suspend_user(uid)
            self._snack("User suspended", ft.Colors.GREEN_800)
            self.load()
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _restore(self, uid: str, api):
        try:
            api.restore_user(uid)
            self._snack("User restored", ft.Colors.GREEN_800)
            self.load()
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

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
                        ft.Text("Could not load users", weight=ft.FontWeight.BOLD),
                        ft.Text(msg, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                        ft.FilledButton("Retry", icon=ft.Icons.REFRESH, on_click=lambda _: self.load()),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
                ),
                alignment=ft.Alignment.CENTER, expand=True,
            )
        ]
        self.list_ref.current.update()
