import flet as ft
from concurrent.futures import ThreadPoolExecutor
from ..tailscale_cli import TailscaleCLI, TailscaleCLIError
from ..api_client import TailscaleAPIClient, TailscaleAPIError
from ..config import load as load_config
from ..acl_resolver import ACLResolver
from ..widgets.peer_tile import peer_tile
from ..services import scan_peer, open_service


class PeersView(ft.Container):
    def __init__(self, cli: TailscaleCLI, api=None):
        super().__init__(expand=True)
        self.cli = cli
        self.api = api
        self._search_query = ""
        self._peer_services: dict[str, list[dict]] = {}
        self._peer_acls: dict[str, list[dict]] = {}
        self._peer_device_details: dict[str, dict] = {}
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
        self._show_loading()
        try:
            status = self.cli.status()
            self._all_peers = status.peers
            self._self_info = status.self_info
            self._render(self._all_devices())
            self._load_acls_async()
            self._load_device_details_async()
        except TailscaleCLIError as e:
            self._show_error(e)

    def _show_loading(self):
        self.list_ref.current.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.ProgressRing(width=32, height=32),
                        ft.Text("Loading peers...", color=ft.Colors.GREY_500, size=14),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
        ]
        self.list_ref.current.update()

    def _load_acls_async(self):
        api = self.api
        if not api or not api.authenticated:
            cfg = load_config()
            if not cfg.get("api_key"):
                return
            api = TailscaleAPIClient(cfg["api_key"], cfg.get("tailnet", ""))

        page = self.page
        if page:
            page.snack_bar = ft.SnackBar(ft.Text("Loading ACL rules..."), duration=10000)
            page.snack_bar.open = True
            page.update()

        def _worker():
            resolver = ACLResolver(api)
            resolver.fetch()
            if not resolver.loaded:
                return
            devices = self._all_devices()
            for p in devices:
                ip = p.get("ip", [""])[0]
                acls = resolver.for_peer(p)
                if acls:
                    self._peer_acls[ip] = acls
            if self._peer_acls:
                all_dev = self._all_devices()
                self._render(
                    all_dev
                    if not self._search_query
                    else [p for p in all_dev if self._search_query in p["name"].lower()]
                )

        import threading
        threading.Thread(target=_worker, daemon=True).start()

    def _load_device_details_async(self):
        api = self.api
        if not api or not api.authenticated:
            cfg = load_config()
            if not cfg.get("api_key"):
                return
            api = TailscaleAPIClient(cfg["api_key"], cfg.get("tailnet", ""))

        def _worker():
            for p in self._all_devices():
                pid = p.get("id", "")
                if not pid:
                    continue
                try:
                    detail = api.get_device(pid)
                    routes = api.get_device_routes(pid)
                    detail["routes"] = routes
                    self._peer_device_details[pid] = detail
                except Exception:
                    pass
            if self._peer_device_details:
                all_dev = self._all_devices()
                self._render(
                    all_dev
                    if not self._search_query
                    else [p for p in all_dev if self._search_query in p["name"].lower()]
                )

        import threading
        threading.Thread(target=_worker, daemon=True).start()

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
                pid = p.get("id", "")
                svcs = self._peer_services.get(ip)
                acls = self._peer_acls.get(ip)
                dev = self._peer_device_details.get(pid)
                tiles.append(
                    peer_tile(
                        p,
                        services=svcs,
                        on_click=lambda _, addr=ip: self._ping(addr),
                        on_open_service=open_service,
                        acls=acls,
                        device_info=dev,
                        on_authorize=(lambda _, d=pid: self._toggle_authorize(d)) if dev else None,
                        on_expire_key=(lambda _, d=pid: self._expire_key(d)) if dev else None,
                        on_edit_tags=(lambda _, d=pid: self._edit_tags_dialog(d)) if dev else None,
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

    def _toggle_authorize(self, device_id: str):
        api = self.api or TailscaleAPIClient(**load_config())
        detail = self._peer_device_details.get(device_id, {})
        new_val = not detail.get("authorized", True)
        try:
            api.authorize_device(device_id, new_val)
            self._snack(f"Device {'authorized' if new_val else 'deauthorized'}", ft.Colors.GREEN_800)
            self.load()
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _expire_key(self, device_id: str):
        api = self.api or TailscaleAPIClient(**load_config())
        try:
            api.expire_device_key(device_id)
            self._snack("Device key expired", ft.Colors.GREEN_800)
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _edit_tags_dialog(self, device_id: str):
        detail = self._peer_device_details.get(device_id, {})
        current = ", ".join(detail.get("tags", []))
        tf = ft.TextField(label="Tags (comma-separated, e.g. tag:server, tag:prod)",
                           value=current, multiline=False, width=400)
        dlg = ft.AlertDialog(
            title=ft.Text("Edit Device Tags"),
            content=tf,
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dlg)),
                ft.FilledButton("Save", on_click=lambda _: self._save_tags(device_id, tf.value, dlg)),
            ],
        )
        if self.page:
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()

    def _save_tags(self, device_id: str, raw: str, dlg: ft.AlertDialog):
        tags = [t.strip() for t in raw.split(",") if t.strip()]
        api = self.api or TailscaleAPIClient(**load_config())
        try:
            api.set_device_tags(device_id, tags)
            dlg.open = False
            self.page.update()
            self._snack("Tags updated", ft.Colors.GREEN_800)
            self.load()
        except TailscaleAPIError as e:
            self._snack(str(e), ft.Colors.RED_800)

    def _close_dialog(self, dlg: ft.AlertDialog):
        dlg.open = False
        if self.page:
            self.page.update()

    def _snack(self, msg: str, color: str):
        if self.page:
            self.page.snack_bar = ft.SnackBar(ft.Text(msg, size=13), bgcolor=color)
            self.page.snack_bar.open = True
            self.page.update()

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
