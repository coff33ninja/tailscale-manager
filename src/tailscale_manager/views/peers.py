import flet as ft
from concurrent.futures import ThreadPoolExecutor
from ..tailscale_cli import TailscaleCLI, TailscaleCLIError
from ..api_client import TailscaleAPIClient, TailscaleAPIError
from ..config import load as load_config
from ..acl_resolver import ACLResolver
from ..widgets.peer_tile import peer_tile
from ..services import scan_peer, open_service


class PeersView(ft.Container):
    def __init__(self, cli: TailscaleCLI):
        super().__init__(expand=True)
        self.cli = cli
        self._search_query = ""
        self._peer_services: dict[str, list[dict]] = {}
        self._peer_acls: dict[str, list[dict]] = {}
        self._self_info: dict | None = None

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
            self._self_info = status.self_info
            self._peer_acls.clear()
            self._render(self._all_devices())
            self._load_acls()
        except TailscaleCLIError as e:
            self._show_error(e)

    def _load_acls(self):
        cfg = load_config()
        api_key = cfg.get("api_key", "")
        tailnet = cfg.get("tailnet", "")
        if not api_key or not tailnet:
            return

        api = TailscaleAPIClient(api_key, tailnet)
        self._resolver = ACLResolver(api)
        self._resolver.fetch()
        if not self._resolver.loaded:
            return

        for p in self._all_devices():
            ip = p.get("ip", [""])[0]
            acls = self._resolver.for_peer(p)
            if acls:
                self._peer_acls[ip] = acls

        if self._peer_acls:
            self._render(self._all_devices() if not self._search_query else [p for p in self._all_devices() if self._search_query in p["name"].lower()])

    def _filter(self, query: str):
        self._search_query = query.lower()
        filtered = [p for p in self._all_devices() if self._search_query in p["name"].lower() or any(self._search_query in ip for ip in p.get("ip", []))]
        self._render(filtered)

    def _scan_all(self):
        online = [p for p in self._all_devices() if p.get("online")]

        page = self.page
        if not page:
            return

        targets = list(online)
        if not targets:
            page.snack_bar = ft.SnackBar(ft.Text("No online targets to scan"), duration=2000)
            page.snack_bar.open = True
            page.update()
            return

        # Show scanning indicator inline
        self.list_ref.current.controls = [
            ft.ProgressRing(width=24, height=24),
            ft.Text(f"Scanning {len(targets)} target(s)...", color=ft.Colors.GREY_500),
        ]
        page.update()

        def _scan_worker():
            found_count = 0
            for t in targets:
                ip = t.get("ip", [""])[0]
                if not ip:
                    continue
                try:
                    svcs = scan_peer(ip, 1.0)
                    if svcs:
                        self._peer_services[ip] = svcs
                        found_count += len(svcs)
                except Exception:
                    pass

            if found_count:
                msg = f"Found {found_count} service(s) on {len(self._peer_services)} device(s)"
            else:
                msg = "No services found"

            # Re-render from the scan thread — all controls are already materialized
            all_devices = self._all_devices()
            self._render(
                all_devices
                if not self._search_query
                else [p for p in all_devices if self._search_query in p["name"].lower()]
            )

            page.snack_bar = ft.SnackBar(ft.Text(msg), duration=4000)
            page.snack_bar.open = True
            page.update()

        import threading
        threading.Thread(target=_scan_worker, daemon=True).start()

    def _all_devices(self) -> list[dict]:
        devices = list(self._all_peers)
        if self._self_info:
            devices.insert(0, self._self_info)
        return devices

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

        online = [p for p in peers if p.get("online")]
        offline = [p for p in peers if not p.get("online")]

        def _make_tiles(plist):
            tiles = []
            for p in plist:
                ip = p.get("ip", [""])[0]
                svcs = self._peer_services.get(ip)
                acls = self._peer_acls.get(ip)
                tiles.append(
                    peer_tile(
                        p,
                        services=svcs,
                        on_click=lambda _, addr=ip: self._ping(addr),
                        on_open_service=open_service,
                        acls=acls,
                    )
                )
            return tiles

        controls: list[ft.Control] = []
        total = len(peers)

        if online:
            controls.append(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color=ft.Colors.GREEN_400),
                        ft.Text(f"Online  {len(online)}", size=13, color=ft.Colors.GREEN_400, weight=ft.FontWeight.W_600),
                    ],
                    spacing=6,
                )
            )
            controls.append(ft.Divider(height=4, color=ft.Colors.with_opacity(0.08, ft.Colors.GREEN)))
            controls.extend(_make_tiles(online))

        if offline:
            if online:
                controls.append(ft.Divider(height=12, color=ft.Colors.with_opacity(0.04, ft.Colors.WHITE)))
            controls.append(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CANCEL, size=14, color=ft.Colors.GREY_500),
                        ft.Text(f"Offline  {len(offline)}", size=13, color=ft.Colors.GREY_500, weight=ft.FontWeight.W_600),
                    ],
                    spacing=6,
                )
            )
            controls.append(ft.Divider(height=4, color=ft.Colors.with_opacity(0.06, ft.Colors.GREY)))
            controls.extend(_make_tiles(offline))

        self.list_ref.current.controls = [
            ft.Text(f"{total} device{'s' if total != 1 else ''}", size=12, color=ft.Colors.GREY_500),
            *controls,
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
