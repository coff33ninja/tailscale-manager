import flet as ft

from .constants import NAV_ITEMS, ROUTES
from .tailscale_cli import TailscaleCLI, get_tailscale_path
from .views.dashboard import DashboardView
from .views.peers import PeersView
from .views.exit_nodes import ExitNodesView
from .views.serve_funnel import ServeFunnelView
from .views.settings import SettingsView
from .views.acls import ACLsView


def main(page: ft.Page):
    page.title = "Tailscale Manager"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window.min_width = 900
    page.window.min_height = 600

    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.BLUE_400,
            primary_container=ft.Colors.BLUE_800,
            secondary=ft.Colors.CYAN_400,
            surface=ft.Colors.GREY_900,
            surface_bright=ft.Colors.GREY_800,
            surface_container=ft.Colors.GREY_800,
            surface_container_high=ft.Colors.GREY_800,
            on_surface=ft.Colors.GREY_100,
            on_surface_variant=ft.Colors.GREY_400,
            outline=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
        ),
        use_material3=True,
    )

    cli = TailscaleCLI(tailscale_path=get_tailscale_path())
    nav_rail_ref = ft.Ref[ft.NavigationRail]()
    content_area = ft.Container(expand=True, padding=20)

    views = {
        ROUTES["dashboard"]: DashboardView(cli),
        ROUTES["peers"]: PeersView(cli),
        ROUTES["exit_nodes"]: ExitNodesView(cli),
        ROUTES["serve"]: ServeFunnelView(cli),
        ROUTES["settings"]: SettingsView(cli),
        ROUTES["acls"]: ACLsView(cli),
    }

    def _navigate(route: str):
        content_area.content = views.get(route, views[ROUTES["dashboard"]])
        content_area.update()
        if content_area.content and hasattr(content_area.content, "load"):
            content_area.content.load()

    def _on_nav_change(e):
        for item in NAV_ITEMS:
            if NAV_ITEMS.index(item) == e.control.selected_index:
                _navigate(item["route"])
                break

    nav_rail = ft.NavigationRail(
        ref=nav_rail_ref,
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        extended=True,
        group_alignment=-0.8,
        on_change=_on_nav_change,
        destinations=[
            ft.NavigationRailDestination(
                icon=getattr(ft.Icons, item["icon"]),
                selected_icon=getattr(ft.Icons, item["icon"]),
                    label=item["label"],
            )
            for item in NAV_ITEMS
        ],
        bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
    )

    page.add(
        ft.Row(
            [
                nav_rail,
                ft.VerticalDivider(width=1),
                content_area,
            ],
            expand=True,
            spacing=0,
        )
    )

    _navigate(ROUTES["dashboard"])
