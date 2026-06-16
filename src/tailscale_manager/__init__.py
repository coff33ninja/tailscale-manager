import flet as ft

from .app import main

def run():
    ft.app(target=main)

__all__ = ["run"]
