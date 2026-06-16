import flet as ft
from concurrent.futures import ThreadPoolExecutor
from ..tailscale_cli import TailscaleCLI, TailscaleCLIError
from ..widgets.peer_tile import peer_tile
from ..services import scan_peer, open_service


class PeersView(ft.Container):
    def __init__(self, cli: TailscaleCLI):
        super().__init__(expand=True)
        self.cli = cli
        self._search_query = ""
        self._peer_services: dict[str, list[dict]] = {}

        self.search_ref = ft.Ref[ft.TextField]()
        self.list_ref = ft.Ref[ft.Column]()

        self.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Peers", size=28, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.IconButton(icon=ft.Icons.WIFI_FIND, tooltip="Scan services",
                                      on_click=lambda _: self._scan_all()),
                        ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda _: self.load()),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text("Devices on your tailnet", size=13, color=ft.Colors.GREY_400),
                ft.Divider(height=16),
                ft.TextField(
                    ref=self.search_ref,
                    hint_text="Search peers...",
                    prefix_icon=ft.Icons.SEARCH,
                    on_change=lambda e: self._filter(e.control.value),
                    border_radius=8,
                    height=44,
                ),
                ft.Divider(height=8, visible=False),
                ft.Column(ref=self.list_ref, spacing=6, scroll=ft.ScrollMode.AUTO, expand=True),
            ],
            spacing=4,
        )
        self._all_peers: list[dict] = []

    def did_mount(self):
        self.load()

    def load(self):
        try:
            status = self.cli.status()
            self._all_peers = status.peers
            self._render(self._all_peers)
        except TailscaleCLIError as e:
            self._show_error(e)

    def _filter(self, query: str):
        self._search_query = query.lower()
        filtered = [p for p in self._all_peers if self._search_query in p["name"].lower() or any(self._search_query in ip for ip in p.get("ip", []))]
        self._render(filtered)

    def _scan_all(self):
        online = [p for p in self._all_peers if p.get("online")]
        if not online:
            page = self.page
            if page:
                page.snack_bar = ft.SnackBar(ft.Text("No online peers to scan"), duration=2000)
                page.snack_bar.open = True
                page.update()
            return

        page = self.page
        if page:
            page.snack_bar = ft.SnackBar(ft.Text(f"Scanning {len(online)} peer(s)..."), duration=5000)
            page.snack_bar.open = True
            page.update()

        def _scan():
            with ThreadPoolExecutor(max_workers=min(len(online), 10)) as pool:
                fut_map = {}
                for p in online:
                    ip = p.get("ip", [""])[0]
                    if ip:
                        fut = pool.submit(scan_peer, ip, 0.8)
                        fut_map[fut] = (ip, p)

                from concurrent.futures import as_completed
                for f in as_completed(fut_map):
                    ip, p = fut_map[f]
                    try:
                        svcs = f.result()
                        if svcs:
                            self._peer_services[ip] = svcs
                    except Exception:
                        pass

            self._render(self._all_peers if not self._search_query else [p for p in self._all_peers if self._search_query in p["name"].lower()])

        import threading
        threading.Thread(target=_scan, daemon=True).start()

    def _render(self, peers: list[dict]):
        if not peers:
            self.list_ref.current.controls = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.PERSON_OFF, size=48, color=ft.Colors.GREY_600),
                            ft.Text("No peers found", color=ft.Colors.GREY_500),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                    ),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                )
            ]
            self.list_ref.current.update()
            return

        tiles = []
        for p in peers:
            ip = p.get("ip", [""])[0]
            svcs = self._peer_services.get(ip)
            tiles.append(
                peer_tile(
                    p,
                    services=svcs,
                    on_click=lambda _, addr=ip: self._ping(addr),
                    on_open_service=open_service,
                )
            )

        self.list_ref.current.controls = [
            ft.Text(f"{len(peers)} peer{'s' if len(peers) != 1 else ''}", size=12, color=ft.Colors.GREY_500),
            *tiles,
        ]
        self.list_ref.current.update()

    def _ping(self, ip: str):
        try:
            result = self.cli.ping(ip)
            page = self.page
            if page:
                page.snack_bar = ft.SnackBar(
                    ft.Text(result[:200]), duration=4000, bgcolor=ft.Colors.GREEN_800
                )
                page.snack_bar.open = True
                page.update()
        except TailscaleCLIError as e:
            page = self.page
            if page:
                page.snack_bar = ft.SnackBar(ft.Text(str(e)), bgcolor=ft.Colors.RED_800)
                page.snack_bar.open = True
                page.update()

    def _show_error(self, e: Exception):
        self.list_ref.current.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.CLOUD_OFF, size=48, color=ft.Colors.RED_400),
                        ft.Text("Could not load peers", weight=ft.FontWeight.BOLD),
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
