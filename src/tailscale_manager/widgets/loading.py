import flet as ft


_GREY = "#9E9E9E"


def loading_view(text: str = "Loading...") -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.ProgressRing(width=32, height=32),
                ft.Text(text, color=_GREY, size=14),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        alignment=ft.Alignment.CENTER,
        expand=True,
    )
