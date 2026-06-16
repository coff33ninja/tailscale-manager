import flet as ft
from ..tailscale_cli import TailscaleCLI, TailscaleCLIError
from ..tailscale_cli import ServeConfig


class ServeFunnelView(ft.Container):
    def __init__(self, cli: TailscaleCLI):
        super().__init__(expand=True)
        self.cli = cli
        self._mode = "serve"
        self.serve_list_ref = ft.Ref[ft.Column]()
        self.funnel_list_ref = ft.Ref[ft.Column]()
        self.add_form_ref = ft.Ref[ft.Column]()
        self.serve_btn = ft.Ref[ft.FilledTonalButton]()
        self.funnel_btn = ft.Ref[ft.FilledTonalButton]()

        self.content = ft.Column(
            [
                ft.Text("Serve & Funnel", size=28, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Expose local services via Tailscale Serve (private) or Funnel (public)",
                    size=13, color=ft.Colors.GREY_400,
                ),
                ft.Divider(height=16),
                ft.Row(
                    [
                        ft.FilledTonalButton(
                            "Serve",
                            ref=self.serve_btn,
                            icon=ft.Icons.LAN,
                            on_click=lambda _: self._switch_mode("serve"),
                        ),
                        ft.FilledTonalButton(
                            "Funnel (Public)",
                            ref=self.funnel_btn,
                            icon=ft.Icons.PUBLIC,
                            on_click=lambda _: self._switch_mode("funnel"),
                        ),
                        ft.Container(expand=True),
                        ft.FilledButton(
                            "Add Route",
                            icon=ft.Icons.ADD,
                            on_click=lambda _: self._show_add_form(),
                        ),
                    ],
                    spacing=8,
                ),
                ft.Divider(height=8),
                ft.Column(ref=self.serve_list_ref, spacing=6, scroll=ft.ScrollMode.AUTO, expand=True),
                ft.Column(ref=self.funnel_list_ref, spacing=6, scroll=ft.ScrollMode.AUTO, expand=True, visible=False),
                ft.Column(ref=self.add_form_ref, spacing=10, visible=False),
            ],
            spacing=4,
        )

    def did_mount(self):
        self.load()

    def load(self):
        self._load_serve()
        self._load_funnel()

    def _switch_mode(self, mode: str):
        self._mode = mode
        is_serve = mode == "serve"
        self.serve_list_ref.current.visible = is_serve
        self.funnel_list_ref.current.visible = not is_serve
        self.add_form_ref.current.visible = False
        self.update()

    def _load_serve(self):
        try:
            config = self.cli.serve_status()
            self._render_serve(config)
        except TailscaleCLIError as e:
            self._render_serve_error(e)

    def _load_funnel(self):
        try:
            config = self.cli.funnel_status()
            self._render_funnel(config)
        except TailscaleCLIError:
            self._render_funnel([])

    def _render_serve(self, config: ServeConfig):
        self.serve_list_ref.current.controls = self._build_route_list(config, "serve")
        self.serve_list_ref.current.update()

    def _render_funnel(self, config):
        self.funnel_list_ref.current.controls = self._build_route_list(config, "funnel")
        self.funnel_list_ref.current.update()

    def _build_route_list(self, config, mode: str):
        controls = []
        if not config.routes:
            controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.LAN if mode == "serve" else ft.Icons.PUBLIC, size=48, color=ft.Colors.GREY_600),
                            ft.Text(f"No {mode} routes configured", color=ft.Colors.GREY_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                    ),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                )
            )
            return controls

        for route in config.routes:
            delete_handler = lambda _, r=route, m=mode: self._delete_route(r, m)
            controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.HTTP if route.get("type") == "web" else ft.Icons.LINK, color=ft.Colors.BLUE_400),
                            ft.Column(
                                [
                                    ft.Text(route.get("source", ""), size=14, weight=ft.FontWeight.W_600),
                                    ft.Text(str(route.get("target", "")), size=12, color=ft.Colors.GREY_400),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400, on_click=delete_handler),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(left=16, top=8, right=16, bottom=8),
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                )
            )
        controls.insert(0, ft.Text(f"{len(config.routes)} route{'s' if len(config.routes) != 1 else ''}", size=12, color=ft.Colors.GREY_500))
        return controls

    def _show_add_form(self):
        source_ref = ft.Ref[ft.TextField]()
        target_ref = ft.Ref[ft.TextField]()
        mode_dd = ft.Ref[ft.Dropdown]()

        self.add_form_ref.current.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Add New Route", size=16, weight=ft.FontWeight.W_600),
                        ft.Dropdown(
                            ref=mode_dd,
                            label="Mode",
                            options=[
                                ft.dropdown.Option("serve", "Serve (Tailnet only)"),
                                ft.dropdown.Option("funnel", "Funnel (Public internet)"),
                            ],
                            value="serve",
                            width=300,
                        ),
                        ft.TextField(ref=source_ref, label="Source Port/Path", hint_text="e.g. 443 or myapp.example.com", width=400),
                        ft.TextField(ref=target_ref, label="Target URL", hint_text="e.g. localhost:3000", width=400),
                        ft.Row(
                            [
                                ft.FilledButton(
                                    "Add Route", icon=ft.Icons.ADD,
                                    on_click=lambda _: self._add_route(
                                        mode_dd.current.value, source_ref.current.value, target_ref.current.value
                                    ),
                                ),
                                ft.TextButton("Cancel", on_click=lambda _: self._cancel_add()),
                            ],
                            spacing=8,
                        ),
                    ],
                    spacing=10,
                ),
                padding=15,
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
            )
        ]
        self.add_form_ref.current.visible = True
        self.add_form_ref.current.update()

    def _cancel_add(self):
        self.add_form_ref.current.visible = False
        self.add_form_ref.current.update()

    def _add_route(self, mode: str, source: str, target: str):
        if not source or not target:
            self._snack("Source and target are required", ft.Colors.RED_800)
            return
        try:
            if mode == "serve":
                self.cli.serve_set(source, target)
            else:
                self.cli.funnel_set(source, target)
            self._snack(f"{mode.capitalize()} route added", ft.Colors.GREEN_800)
            self._cancel_add()
            self.load()
        except TailscaleCLIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _delete_route(self, route: dict, mode: str):
        try:
            source = route.get("source", "")
            if mode == "serve":
                self.cli.serve_remove(source)
            else:
                self.cli.funnel_set(source, "", on=False)
            self._snack("Route removed", ft.Colors.GREEN_800)
            self.load()
        except TailscaleCLIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _snack(self, msg: str, color: str):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
            self.page.snack_bar.open = True
            self.page.update()

    def _render_serve_error(self, e: Exception):
        self.serve_list_ref.current.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=ft.Colors.RED_400),
                        ft.Text("Could not load Serve config", weight=ft.FontWeight.BOLD),
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
        self.serve_list_ref.current.update()
