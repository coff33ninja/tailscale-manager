import flet as ft
from ..api_client import TailscaleAPIClient, TailscaleAPIError
from ..config import load as load_config


class DNSView(ft.Container):
    def __init__(self, cli, api=None):
        super().__init__(expand=True)
        self.cli = cli
        self.api = api

        self.tabs = ft.Tabs(
            length=4,
            selected_index=0,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Nameservers"),
                            ft.Tab(label="Preferences"),
                            ft.Tab(label="Search Paths"),
                            ft.Tab(label="Split DNS"),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            self._build_ns_tab(),
                            self._build_prefs_tab(),
                            self._build_paths_tab(),
                            self._build_split_tab(),
                        ]
                    ),
                ]
            ),
        )

        self.content = ft.Column(
            [
                ft.Text("DNS", size=28, weight=ft.FontWeight.BOLD),
                ft.Text("Manage tailnet DNS configuration", size=13, color=ft.Colors.GREY_400),
                ft.Divider(height=16),
                self.tabs,
            ],
            spacing=4,
        )

    def did_mount(self):
        self.load()

    def load(self):
        self._load_all()

    # ── Helpers ──

    def _get_api(self):
        if self.api and self.api.authenticated:
            return self.api
        cfg = load_config()
        if cfg.get("api_key"):
            return TailscaleAPIClient(cfg["api_key"], cfg.get("tailnet", ""))
        return None

    # ── Nameservers tab ──

    def _build_ns_tab(self):
        self.ns_ref = ft.Ref[ft.Column]()
        self.ns_input = ft.Ref[ft.TextField]()
        return ft.Column([
            ft.Row([
                ft.TextField(ref=self.ns_input, label="Add nameserver", hint_text="e.g. 1.1.1.1", width=300, height=44,
                             on_submit=lambda _: self._add_ns()),
                ft.FilledButton("Add", icon=ft.Icons.ADD, on_click=lambda _: self._add_ns()),
                ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda _: self._load_ns()),
            ], spacing=8),
            ft.Divider(height=8),
            ft.Column(ref=self.ns_ref, spacing=6, expand=True, scroll=ft.ScrollMode.AUTO),
        ], spacing=4, expand=True)

    def _load_ns(self):
        api = self._get_api()
        if not api:
            self.ns_ref.current.controls = [ft.Text("API not configured", color=ft.Colors.GREY_500)]
            self.ns_ref.current.update()
            return
        try:
            ns = api.list_dns_nameservers()
            self._render_ns(ns)
        except TailscaleAPIError as e:
            self._show_error(self.ns_ref, str(e))

    def _render_ns(self, ns: list):
        if not ns:
            self.ns_ref.current.controls = [ft.Text("No custom nameservers set", color=ft.Colors.GREY_500)]
            self.ns_ref.current.update()
            return
        chips = []
        for n in ns:
            chips.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(n, size=13, font_family="monospace"),
                        ft.IconButton(icon=ft.Icons.CLOSE, icon_size=14, height=24, width=24,
                                      data=n, on_click=lambda e: self._remove_ns(e.control.data)),
                    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(left=8, top=4, right=4, bottom=4),
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                )
            )
        self.ns_ref.current.controls = [
            ft.Text(f"{len(ns)} nameserver{'s' if len(ns)!=1 else ''}", size=12, color=ft.Colors.GREY_500),
            ft.Row(chips, spacing=6, wrap=True),
        ]
        self.ns_ref.current.update()

    def _add_ns(self):
        val = (self.ns_input.current.value or "").strip()
        if not val:
            return
        api = self._get_api()
        if not api:
            return
        try:
            current = api.list_dns_nameservers()
            updated = list(set(current + [val]))
            api.set_dns_nameservers(updated)
            self.ns_input.current.value = ""
            self.ns_input.current.update()
            self._load_ns()
            self._snack(f"Added {val}", ft.Colors.GREEN_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _remove_ns(self, val: str):
        api = self._get_api()
        if not api:
            return
        try:
            current = api.list_dns_nameservers()
            updated = [n for n in current if n != val]
            api.set_dns_nameservers(updated)
            self._load_ns()
            self._snack(f"Removed {val}", ft.Colors.GREEN_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    # ── Preferences tab ──

    def _build_prefs_tab(self):
        self.magic_switch = ft.Ref[ft.Switch]()
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("MagicDNS", size=16, weight=ft.FontWeight.W_600),
                    ft.Text("Automatically register DNS names for devices in your tailnet", size=11, color=ft.Colors.GREY_500),
                    ft.Switch(ref=self.magic_switch, label="Enabled", on_change=lambda _: self._save_prefs()),
                ], spacing=6),
                padding=15, border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
            ),
        ], spacing=4, expand=True)

    def _load_prefs(self):
        api = self._get_api()
        if not api:
            return
        try:
            prefs = api.get_dns_preferences()
            val = prefs.get("magicDNS", prefs.get("magicDns", True))
            self.magic_switch.current.value = bool(val)
            self.magic_switch.current.update()
        except TailscaleAPIError:
            pass

    def _save_prefs(self):
        api = self._get_api()
        if not api:
            return
        try:
            api.set_dns_preferences(self.magic_switch.current.value)
            self._snack("DNS preferences saved", ft.Colors.GREEN_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    # ── Search Paths tab ──

    def _build_paths_tab(self):
        self.paths_ref = ft.Ref[ft.Column]()
        self.path_input = ft.Ref[ft.TextField]()
        return ft.Column([
            ft.Row([
                ft.TextField(ref=self.path_input, label="Add search path", hint_text="e.g. example.com", width=300, height=44,
                             on_submit=lambda _: self._add_path()),
                ft.FilledButton("Add", icon=ft.Icons.ADD, on_click=lambda _: self._add_path()),
                ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda _: self._load_paths()),
            ], spacing=8),
            ft.Divider(height=8),
            ft.Column(ref=self.paths_ref, spacing=6, expand=True, scroll=ft.ScrollMode.AUTO),
        ], spacing=4, expand=True)

    def _load_paths(self):
        api = self._get_api()
        if not api:
            return
        try:
            paths = api.get_dns_search_paths()
            self._render_paths(paths)
        except TailscaleAPIError as e:
            self._show_error(self.paths_ref, str(e))

    def _render_paths(self, paths: list):
        if not paths:
            self.paths_ref.current.controls = [ft.Text("No search paths set", color=ft.Colors.GREY_500)]
            self.paths_ref.current.update()
            return
        chips = []
        for p in paths:
            chips.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(p, size=13),
                        ft.IconButton(icon=ft.Icons.CLOSE, icon_size=14, height=24, width=24,
                                      data=p, on_click=lambda e: self._remove_path(e.control.data)),
                    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(left=8, top=4, right=4, bottom=4),
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                )
            )
        self.paths_ref.current.controls = [
            ft.Text(f"{len(paths)} path{'s' if len(paths)!=1 else ''}", size=12, color=ft.Colors.GREY_500),
            ft.Row(chips, spacing=6, wrap=True),
        ]
        self.paths_ref.current.update()

    def _add_path(self):
        val = (self.path_input.current.value or "").strip()
        if not val:
            return
        api = self._get_api()
        if not api:
            return
        try:
            current = api.get_dns_search_paths()
            updated = list(set(current + [val]))
            api.set_dns_search_paths(updated)
            self.path_input.current.value = ""
            self.path_input.current.update()
            self._load_paths()
            self._snack(f"Added {val}", ft.Colors.GREEN_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _remove_path(self, val: str):
        api = self._get_api()
        if not api:
            return
        try:
            current = api.get_dns_search_paths()
            updated = [p for p in current if p != val]
            api.set_dns_search_paths(updated)
            self._load_paths()
            self._snack(f"Removed {val}", ft.Colors.GREEN_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    # ── Split DNS tab ──

    def _build_split_tab(self):
        self.split_ref = ft.Ref[ft.Column]()
        self.split_domain_ref = ft.Ref[ft.TextField]()
        self.split_ns_ref = ft.Ref[ft.TextField]()
        return ft.Column([
            ft.Row([
                ft.TextField(ref=self.split_domain_ref, label="Domain", hint_text="e.g. example.com", width=250, height=44),
                ft.TextField(ref=self.split_ns_ref, label="Nameservers (comma-separated)", hint_text="1.1.1.1, 8.8.8.8",
                             width=300, height=44, on_submit=lambda _: self._add_split()),
                ft.FilledButton("Add", icon=ft.Icons.ADD, on_click=lambda _: self._add_split()),
                ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda _: self._load_split()),
            ], spacing=8, wrap=True),
            ft.Divider(height=8),
            ft.Column(ref=self.split_ref, spacing=6, expand=True, scroll=ft.ScrollMode.AUTO),
        ], spacing=4, expand=True)

    def _load_split(self):
        api = self._get_api()
        if not api:
            return
        try:
            sd = api.get_split_dns()
            self._render_split(sd)
        except TailscaleAPIError as e:
            self._show_error(self.split_ref, str(e))

    def _render_split(self, sd: dict):
        if not sd:
            self.split_ref.current.controls = [ft.Text("No split DNS routes configured", color=ft.Colors.GREY_500)]
            self.split_ref.current.update()
            return
        tiles = []
        for domain, nss in sd.items():
            ns_text = ", ".join(nss) if isinstance(nss, list) else str(nss)
            tiles.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(domain, size=14, weight=ft.FontWeight.W_600),
                            ft.Text(ns_text, size=11, color=ft.Colors.GREY_500),
                        ], spacing=2, expand=True),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400, icon_size=18,
                                      tooltip="Remove", data=domain,
                                      on_click=lambda e: self._delete_split(e.control.data)),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(left=16, top=8, right=8, bottom=8),
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                )
            )
        self.split_ref.current.controls = [
            ft.Text(f"{len(sd)} route{'s' if len(sd)!=1 else ''}", size=12, color=ft.Colors.GREY_500),
            *tiles,
        ]
        self.split_ref.current.update()

    def _add_split(self):
        domain = (self.split_domain_ref.current.value or "").strip()
        raw = (self.split_ns_ref.current.value or "").strip()
        if not domain or not raw:
            return
        nss = [n.strip() for n in raw.split(",") if n.strip()]
        api = self._get_api()
        if not api:
            return
        try:
            api.set_split_dns(domain, nss)
            self.split_domain_ref.current.value = ""
            self.split_ns_ref.current.value = ""
            self.split_domain_ref.current.update()
            self.split_ns_ref.current.update()
            self._load_split()
            self._snack(f"Split DNS added for {domain}", ft.Colors.GREEN_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _delete_split(self, domain: str):
        api = self._get_api()
        if not api:
            return
        try:
            api.delete_split_dns(domain)
            self._load_split()
            self._snack(f"Removed split DNS for {domain}", ft.Colors.GREEN_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    # ── Load all tabs ──

    def _load_all(self):
        self._load_ns()
        self._load_prefs()
        self._load_paths()
        self._load_split()

    # ── Shared ──

    def _show_error(self, ref, msg: str):
        ref.current.controls = [ft.Text(msg, color=ft.Colors.RED_400)]
        ref.current.update()

    def _snack(self, msg: str, color: str):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msg, size=13), bgcolor=color)
            self.page.snack_bar.open = True
            self.page.update()
