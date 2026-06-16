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
                        ft.Text(title, size=13, color="#9E9E9E"),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                ft.Text(subtitle, size=11, color="#757575", visible=bool(subtitle)),
            ],
            spacing=4,
            expand=True,
        ),
        padding=15,
        border_radius=12,
        bgcolor="#2A2A3E",
        border=ft.Border(
            left=ft.BorderSide(1, "#3A3A5E"),
            top=ft.BorderSide(1, "#3A3A5E"),
            right=ft.BorderSide(1, "#3A3A5E"),
            bottom=ft.BorderSide(1, "#3A3A5E"),
        ),
        expand=True,
    )
