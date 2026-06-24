"""
PackageInfo Controller.
"""

import flet as ft
from fletx.core import FletXPage
from fletx.navigation import go_back

from ..controllers.package_info_controller import PackageInfoController
from ..models.package_model import PackageModel


class PackageInfoPage(FletXPage):
    """PackageInfo Page"""

    def __init__(self):
        # print("PackageInfoPage:__init__")
        super().__init__()
        self.controller = PackageInfoController()

    def on_init(self):
        """Hook called when PackageInfoPage is initialized"""
        # print("PackageInfoPage:on_init")

    def on_destroy(self):
        """Hook called when PackageInfoPage will be unmounted."""
        # print("PackageInfoPage:on_destroy")

    def _on_title_click(self):
        go_back()

    def build_app_bar(self):
        return ft.AppBar(title=ft.Text("Package Infomation"), bgcolor=ft.Colors.SURFACE)

    def build(self) -> ft.Control:
        """Method that build PackageInfoPage content"""
        # print("PackageInfoPage:build")
        routing_param_data = self.route_info.data
        package: PackageModel = routing_param_data.get("package")
        info = self.controller.get_package_info(package)
        return ft.Column(
            [
                ft.TextButton(
                    content=ft.Text("← Package Infomation", size=20),
                    on_click=lambda e: self._on_title_click(),
                ),
                ft.Divider(),
                ft.Column(
                    spacing=5,
                    controls=[
                        ft.Text(info.display, size=20, weight=ft.FontWeight.BOLD),
                        ft.Text(info.description, size=14),
                        ft.Text(f"Version: {info.version}"),
                        ft.Text(f"License: {info.license}"),
                        ft.Row(
                            spacing=0,
                            controls=[
                                ft.Text(f"Site: "),
                                ft.TextButton(info.site, on_click=lambda e: self.page.launch_url(info.site)),
                            ],
                        ),
                        ft.Text(f"Process time: {info.process_time}"),
                        ft.Divider(),
                    ],
                ),
                ft.Text("Details:", size=16, weight=ft.FontWeight.BOLD),
                # Markdown 表示
                ft.Column(
                    controls=[
                        ft.Markdown(
                            info.markdown,
                            selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            code_theme=ft.MarkdownCodeTheme.NIGHT_OWL,
                            on_tap_link=lambda e: self.page.launch_url(str(e.data)),
                        )
                    ],
                    expand=True,
                    scroll=ft.ScrollMode.ALWAYS,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
            ],
            expand=True,
            spacing=1,
        )
