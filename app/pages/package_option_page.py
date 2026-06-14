"""
PackageOption Page.
"""

import flet as ft
from fletx.core import FletXPage
from fletx.decorators import obx
from fletx.navigation import go_back

from ..controllers.package_option_controller import PackageOptionController
from ..models.package_model import PackageModel
from ..models.package_option_ui_model import OptionUiItem


class PackageOptionPage(FletXPage):
    """PackageInfo Page"""

    def __init__(self):
        self.initialized = False
        print("PackageOptionPage:__init__")
        super().__init__()
        self.controller = PackageOptionController()

    def on_init(self):
        """Hook called when PackageOptionPage is initialized"""
        # print("PackageOptionPage:on_init"
        self.update_diabled()

    def _on_loaded(self, d):
        # print("PackageOptionPage:_on_loaded")
        self.refresh()

    def on_destroy(self):
        """Hook called when PackageOptionPage will be unmounted."""
        # print("PackageOptionPage:on_destroy")

    def on_change_bgcolor(self, e):
        e.control.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST if e.data == "true" else ft.Colors.SURFACE
        e.control.update()

    def update_diabled(self):
        items = self.content.controls[2].controls
        for item in items:
            name = item.widget.data
            disabled = self.controller.disabled.get(name, True)
            item.widget.content.controls[1].disabled = disabled

        self.refresh()

    def _on_change(self, event):
        # save button
        self.content.controls[4].controls[1].controls[1].disabled = False

        self.update_diabled()
        self.refresh()

    def _on_click_save(self, event):
        # save button
        self.content.controls[4].controls[1].controls[1].disabled = True
        self.refresh()

    def _on_title_click(self):
        go_back()

    @obx
    def display_option_item(self, ui: OptionUiItem):
        # print("PackageOptionPage:display_option_item")

        if ui.type == "choice":
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(value=ui.display, size=16),
                        ft.Dropdown(
                            width=250,
                            value=self.controller.values.value.get(ui.name),
                            options=[ft.dropdown.Option(x) for x in ui.items],
                            on_change=lambda e: [
                                self.controller.update_value(ui.name, e.control.value),
                                self._on_change(e),
                            ],
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                data=ui.name,
                padding=ft.padding.symmetric(horizontal=20),
                on_hover=self.on_change_bgcolor,
            )
        if ui.type == "bool":
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(value=ui.display, size=16),
                        ft.Switch(
                            value=self.controller.values.value.get(ui.name, False),
                            on_change=lambda e: [
                                self.controller.update_value(ui.name, e.control.value),
                                self._on_change(e),
                            ],
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                data=ui.name,
                padding=ft.padding.symmetric(horizontal=20),
                on_hover=self.on_change_bgcolor,
            )
        else:  # text
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(value=ui.display, size=16),
                        ft.TextField(
                            width=250,
                            value=self.controller.values.value.get(ui.name),
                            on_change=lambda e: [
                                self.controller.update_value(ui.name, e.control.value),
                                self._on_change(e),
                            ],
                            #  disabled=self.controller.disabled.value.get(ui.name, True),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                data=ui.name,
                padding=ft.padding.symmetric(horizontal=20),
                on_hover=self.on_change_bgcolor,
            )

    @obx
    def display_option_list(self):
        # print("PackageOptionPage:display_option_list")
        return ft.ListView(
            [self.display_option_item(ui) for ui in self.controller.option_ui.value],
            auto_scroll=False,
            expand=True,
        )

    def build(self):
        """Method that build PackageOptionPage content"""
        # print("PackageOptionPage:build")
        if not self.initialized:
            routing_param_data = self.route_info.data
            package: PackageModel = routing_param_data.get("package")
            self.controller.load_option(package)
            self.initialized = True
        return ft.Column(
            [
                ft.TextButton(
                    content=ft.Text(f"Package Option: {self.controller.package.display}", size=20),
                    on_click=lambda e: self._on_title_click(),
                ),
                ft.Divider(),
                self.display_option_list(),
                ft.Divider(),
                ft.Row(
                    controls=[
                        ft.ElevatedButton("Revert", on_click=lambda e: [self.controller.revert(), self._on_change(e)]),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Reset", on_click=lambda e: [self.controller.reset(), self._on_change(e)]
                                ),
                                ft.ElevatedButton(
                                    "Save",
                                    disabled=True,
                                    on_click=lambda e: [self.controller.save(), self._on_click_save(e)],
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=1,
        )
