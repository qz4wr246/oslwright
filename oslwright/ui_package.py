import asyncio

import flet as ft
from click import style

from oslwright.ow_package import Package
from oslwright.ow_platform import Platform, Reason, ReasonCode
from oslwright.ow_utils import Post, Shell


class uiPackageItem(ft.Container):
    def __init__(self, package: Package, odd: bool = True):
        super().__init__()
        self.package: Package = package
        self.clicked = False

        self.check_box = ft.Checkbox(
            label=self.package.display,
            label_style=ft.TextStyle(size=18),
            value=self.clicked,
            on_change=self.on_change_checkbox,
        )
        self.txt_version = ft.Text(
            f"version: {self.package.settings['version']}",
            theme_style=ft.TextThemeStyle.BODY_MEDIUM,
        )
        info = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                ft.Row(
                    controls=[
                        self.txt_version,
                        ft.Text(f"license: {self.package.license}", theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                    ]
                ),
                ft.Text(
                    value=self.package.description,
                    theme_style=ft.TextThemeStyle.BODY_SMALL,
                    italic=True,
                    max_lines=2,
                    no_wrap=False,
                ),
            ],
        )
        buttons = ft.Row(
            spacing=0,
            controls=[
                ft.IconButton(icon=ft.Icons.INFO_OUTLINE_ROUNDED, on_click=self.on_click_info),
                ft.IconButton(icon=ft.Icons.SETTINGS_ROUNDED, on_click=self.on_click_setting),
                ft.IconButton(icon=ft.Icons.CONSTRUCTION_ROUNDED, on_click=self.on_click_construction),
            ],
            alignment=ft.MainAxisAlignment.START,
        )
        self.content = ft.Row(
            controls=[ft.Row(controls=[self.check_box], width=260), info, buttons],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        self.padding = ft.padding.only(right=10)
        self.on_hover = self.on_change_bgcolor

    def on_change_bgcolor(self, e):
        e.control.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST if e.data == "true" else ft.Colors.SURFACE
        e.control.update()

    def on_change_checkbox(self, e):
        self.clicked = e.data == "true"

    def on_click_construction(self, e):
        self.page.views[-1].data = [self.package]
        self.page.go("/build")

    def on_click_setting(self, e):
        self.page.views[-1].data = self.package
        self.page.go("/settings")

    def on_click_info(self, e):
        self.page.views[-1].data = self.package
        self.page.go("/info")

    def change_checkbox(self, value: bool):
        self.clicked = value
        self.check_box.value = value
        self.check_box.update()


class uiPackageArea(ft.Column):

    def __init__(self, platform: Platform):
        super().__init__()
        self.all_clicked = False
        self.package_list = None
        self.package_area = None
        self.packages: list[Package] = []
        self.platform = platform

        self.reload_button = ft.ElevatedButton("Reload", icon=ft.Icons.REFRESH, on_click=self.on_reload)
        self.default_settings_button = ft.ElevatedButton(
            "Setting", icon=ft.Icons.SETTINGS_ROUNDED, on_click=self.on_default_settings
        )
        self.build_all_button = ft.ElevatedButton(
            "Build all", icon=ft.Icons.CONSTRUCTION, on_click=self.on_click_build_all
        )
        package_head = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Checkbox("Check", value=self.all_clicked, on_change=self.on_click_checkbox_all),
                ft.Row(controls=[self.default_settings_button, self.build_all_button]),
            ],
        )

        self.package_list = ft.Column(
            expand=True,
            spacing=1,
            scroll=ft.ScrollMode.ALWAYS,
        )

        for package in self.packages:
            self.package_list.controls.append(uiPackageItem(package))

        self.controls = [package_head, self.package_list]
        self.alignment = ft.MainAxisAlignment.SPACE_BETWEEN

    def on_click_build_all(self, e):
        bld_pkgs = []
        if self.package_list:
            for item in self.package_list.controls:
                if item.clicked:
                    bld_pkgs.append(item.package)
        if len(bld_pkgs):
            self.page.views[-1].data = bld_pkgs
            self.page.go("/build")

    def on_reload(self, e):
        for package in self.packages:
            package.Reload()

    def on_default_settings(self, e):
        self.page.views[-1].data = (self.platform, self.packages)
        self.page.go("/default_settings")

    def on_click_checkbox_all(self, e):
        self.all_clicked = e.data == "true"
        if self.package_list:
            for item in self.package_list.controls:
                item.change_checkbox(e.data == "true")

    def setPackages(self, packages: list[Package]):
        if not packages or len(packages) == 0:
            self.build_all_button.disabled = True
            self.reload_button.disabled = True
            return
        self.packages = packages
        self.package_list.controls = []
        i = 0
        for package in self.packages:
            self.package_list.controls.append(uiPackageItem(package, bool(i % 2)))
            i += 1
        self.build_all_button.disabled = False
        self.reload_button.disabled = False
        self.update()


class uiPackageView(ft.View):

    def __init__(self, platform):
        self.init_platform = False
        self.platform = platform
        self.packages: list[Package] = []

        self.package_area = uiPackageArea(platform)
        self.package_area.expand = True

        controls = [
            ft.AppBar(title=ft.Text("Select Pacakge"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST),
            ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[self.package_area],
            ),
        ]
        super().__init__("/", controls=controls)
        self.vertical_alignment = ft.MainAxisAlignment.SPACE_BETWEEN

        self.verbose = False

    def did_mount(self):
        if not self.init_platform:
            asyncio.run(self.startup_task())

    async def startup_task(self):
        def exit_app(page):
            page.close(dlg_modal)
            page.window.destroy()

        reason = self.platform.CheckPlatform()
        if reason.code == ReasonCode.COMPLETE:
            self.packages = self.platform.LoadPackages()
            self.package_area.setPackages(self.packages)
            return
        elif reason.code == ReasonCode.MISSING_VISUALSTUDIO:
            dlg_modal = ft.AlertDialog(
                modal=True,
                title=ft.Text("Alert"),
                content=ft.Text("Please Install Visual Studio.\n and restart this application."),
                actions=[ft.TextButton("Exit", on_click=lambda e: exit_app(e.page))],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.open(dlg_modal)
            self.page.update()
            return
        elif reason.code == ReasonCode.MISSING_BASE_TOOLS:
            dlg_modal = ft.AlertDialog(
                modal=True,
                title=ft.Text("Alert"),
                content=ft.Text(
                    f"Please install the following missing tools.\n and restart this application.\n\n{reason.message}\n"
                ),
                actions=[ft.TextButton("Exit", on_click=lambda e: exit_app(e.page))],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.open(dlg_modal)
            self.page.update()
            return

        elif reason.code == ReasonCode.MISSING_EMBEDDED_TOOLS:
            dlg_modal = ft.AlertDialog(
                modal=True,
                title=ft.Text("Alert"),
                content=ft.Text(
                    f"The following tools are not installed.\n\n{reason.message}\n Please press the install tools button.\n"
                ),
                actions=[
                    ft.TextButton(
                        "Install tools and exit", on_click=lambda e: e.page.close_dialog() or self.install_tools()
                    ),
                    ft.TextButton("Exit", on_click=lambda e: exit_app(e.page)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.open(dlg_modal)
            self.page.update()
            return
        self.update()

    def install_tools(self):
        pkgs = self.platform.GetToolsPackage()
        if pkgs:
            self.page.views[-1].data = (pkgs, True)
            self.page.go("/build")
        self.page.window.destroy()
