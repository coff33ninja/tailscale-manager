import flet as ft
from ..tailscale_cli import TailscaleCLI, TailscaleCLIError


class ExitNodesView(ft.Container):
    def __init__(self, cli: TailscaleCLI, api=None):
        super().__init__(expand=True)
        self.cli = cli
        self.api = api
        self.list_ref = ft.Ref[ft.Column]()

        self.content = ft.Column(
            [
                ft.Text("Exit Nodes", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Route traffic through another device on your tailnet", size=13, color=ft.Colors.GREY_400),
                ft.Divider(height=16),
                ft.Row(
                    [
                        ft.FilledButton("Disable Exit Node", icon=ft.Icons.EXIT_TO_APP, on_click=lambda _: self._disable()),
                        ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda _: self.load()),
                    ],
                    spacing=8,
                ),
                ft.Divider(height=8),
                ft.Column(ref=self.list_ref, spacing=6, scroll=ft.ScrollMode.AUTO, expand=True),
            ],
            spacing=4,
        )
        self._exit_nodes: list[dict] = []

    def did_mount(self):
        self.load()

    def load(self):
        try:
            status = self.cli.status()
            self._exit_nodes = [p for p in status.peers if p.get("exit_node") or p.get("exit_node_allow")]
            self._render()
        except TailscaleCLIError as e:
            self._show_error(e)

    def _render(self):
        if not self._exit_nodes:
            self.list_ref.current.controls = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.EXIT_TO_APP, size=64, color=ft.Colors.GREY_600),
                            ft.Text("No exit nodes available", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                "Exit nodes must be configured on another device in your tailnet",
                                color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                )
            ]
            self.list_ref.current.update()
            return

        tiles = []
        for node in self._exit_nodes:
            is_active = node.get("exit_node", False)
            tiles.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.CHECK_CIRCLE if is_active else ft.Icons.RADIO_BUTTON_UNCHECKED,
                                    color=ft.Colors.GREEN_400 if is_active else ft.Colors.GREY_500,
                                    size=22,
                                ),
                                width=40,
                            ),
                            ft.Column(
                                [
                                    ft.Text(node.get("name", ""), size=15, weight=ft.FontWeight.W_600),
                                    ft.Text(", ".join(node.get("ip", [])), size=12, color=ft.Colors.GREY_400),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.FilledTonalButton(
                                "Use",
                                data=node,
                                on_click=lambda e, n=node: self._enable(n),
                                visible=not is_active,
                            ),
                            ft.Container(
                                content=ft.Text("Active", size=12, color=ft.Colors.GREEN_400, weight=ft.FontWeight.W_600),
                                visible=is_active,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(left=16, top=12, right=16, bottom=12),
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                    border=ft.Border(top=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), right=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), bottom=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)), left=ft.BorderSide(0.5, ft.Colors.with_opacity(0.08, ft.Colors.WHITE))),
                )
            )

        self.list_ref.current.controls = [
            ft.Text(f"{len(self._exit_nodes)} exit node{'s' if len(self._exit_nodes) != 1 else ''}", size=12, color=ft.Colors.GREY_500),
            *tiles,
        ]
        self.list_ref.current.update()

    def _enable(self, node: dict):
        try:
            ip = node.get("ip", [""])[0]
            self.cli.up(exit_node=ip)
            self.load()
            self._snack(f"Exit node set to {node.get('name', ip)}", ft.Colors.GREEN_800)
        except TailscaleCLIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _disable(self):
        try:
            self.cli.up()
            self.load()
            self._snack("Exit node disabled", ft.Colors.GREEN_800)
        except TailscaleCLIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _snack(self, msg: str, color: str):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
            self.page.snack_bar.open = True
            self.page.update()

    def _show_error(self, e: Exception):
        self.list_ref.current.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=ft.Colors.RED_400),
                        ft.Text("Could not load exit nodes", weight=ft.FontWeight.BOLD),
                        ft.Text(str(e), color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                        ft.FilledButton("Retry", icon=ft.Icons.REFRESH, on_click=lambda _: self.load()),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
        ]
        self.list_ref.current.update()
