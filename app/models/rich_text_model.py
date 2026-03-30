from dataclasses import dataclass
import flet as ft


@dataclass
class RichText:
    text: str = ""
    color: ft.Colors = ft.Colors.ON_SURFACE
