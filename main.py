"""
Oslwright Application
"""

import os
import subprocess

import flet as ft
from fletx.app import FletXApp

from app.core.constants import Routes
from app.core.theme import dark_theme, light_theme
from app.routes import setup_routes
from app.services import register_services


def main():
    """Main entry point for the Oslwright application."""
    subprocess.run(["chcp.com", "65001"])
    os.environ["PYTHONUTF8"] = "1"

    register_services()
    setup_routes()

    # App Configuration
    app = FletXApp(
        title="OSLwright the open source library builder",
        initial_route=Routes.HOME,
        debug=False,
        theme=light_theme,
        dark_theme=dark_theme,
        theme_mode=ft.ThemeMode.DARK,
        window_config={"width": 1000, "height": 800, "resizable": True, "maximizable": True},
    )

    # Run App
    app.run()


if __name__ == "__main__":
    main()
