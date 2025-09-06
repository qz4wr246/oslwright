import os

import flet as ft

from oslwright.ow_package import Package


class uiInfo(ft.Container):
    def __init__(self, package: Package):
        super().__init__()
        self.package = package
        self.content = ft.Column(
            controls=[
                ft.Text(self.package.description),
                ft.Text(f"version: {self.package.settings['version']}"),
                ft.Text(f"license: {self.package.license}"),
                ft.Row(
                    controls=[
                        ft.Text("site: "),
                        ft.TextButton(
                            text=self.package.site,
                            url=self.package.site,
                        ),
                    ]
                ),
                ft.Divider(height=1),
                ft.Column(
                    controls=[
                        ft.Markdown(
                            value=package.GetInfoText(),
                            selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
                            code_theme="night-owl",
                            on_tap_link=lambda e: self.page.launch_url(e.data),
                        )
                    ],
                    expand=True,
                    scroll=ft.ScrollMode.ALWAYS,
                ),
            ],
            expand=True,
            spacing=1,
        )
        self.expand = True


class uiInfoView(ft.View):
    def __init__(self, package: Package):
        controls = [
            ft.AppBar(title=ft.Text(f"Info : {package.display}"), bgcolor=ft.colors.SURFACE_VARIANT),
            uiInfo(package),
        ]
        super().__init__("/info", controls=controls)
