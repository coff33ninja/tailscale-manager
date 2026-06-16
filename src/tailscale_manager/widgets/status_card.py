import flet as ft
from ..constants import STATUS_COLORS


def status_card(
    title: str,
    value: str,
    icon: str = "INFO",
    status: str = "online",
    subtitle: str = "",
) -> ft.Container:
    color = STATUS_COLORS.get(status, STATUS_COLORS["unknown"])
    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(icon, color=color, size=20),
                        ft.Text(title, size=13, color=ft.Colors.GREY_400),
                    ],
                    spacing=4,
                ),
                ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text(subtitle, size=11, color=ft.Colors.GREY_500, visible=bool(subtitle)),
            ],
            spacing=4,
        ),
        padding=15,
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.PRIMARY),
        border=ft.Border(top=ft.BorderSide(1, ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY)), right=ft.BorderSide(1, ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY)), bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY)), left=ft.BorderSide(1, ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY))),
        expand=True,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
    )
