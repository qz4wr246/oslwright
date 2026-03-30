"""
AppSetting Page.
"""

from typing import Any, Dict

import flet as ft
from fletx.core import FletXPage
from fletx.decorators import obx
from fletx.navigation import go_back

from ..controllers.app_setting_controller import AppSettingController


class AppSettingPage(FletXPage):
    """AppSetting Page"""

    def __init__(self):
        # print("AppSettingPage:__init__")
        super().__init__()

        self.controller = AppSettingController()
        self.controller.load_setting()

    def on_init(self):
        """Hook called when AppSettingPage is initialized"""
        # print("AppSettingPage:on_init")
        pass

    def on_destroy(self):
        """Hook called when AppSettingPage will be unmounted."""
        # print("AppSettingPage:on_destroy")
        pass

    def on_change_bgcolor(self, e):
        e.control.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST if e.data == "true" else ft.Colors.SURFACE
        e.control.update()

    def _on_change(self, event):
        # save button
        self.content.controls[4].controls[1].disabled = False
        self.refresh()

    def _on_click_save(self, event):
        # save button
        self.content.controls[4].controls[1].disabled = True
        self.refresh()

    def build_app_bar(self):
        """Override to create app bar"""
        return ft.AppBar(
            title=ft.Text("System Setting"),
            center_title=True,
            actions=[
                ft.IconButton(icon=ft.Icons.HELP_OUTLINE),
            ],
        )

    def _on_title_click(self):
        go_back()

    @obx
    def display_setting_item(self, ui: Dict[str, Any]):
        # print("AppSettingPage:display_setting_item")

        if ui["type"] == "choice":
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(value=ui["display"], size=16),
                        ft.Dropdown(
                            width=250,
                            value=self.controller.values.value.get(ui["name"]),
                            options=[ft.dropdown.Option(x) for x in ui["items"]],
                            on_change=lambda e: [
                                self.controller.update_value(ui["name"], e.control.value),
                                self._on_change(e),
                            ],
                            disabled=not (ui["enable"]),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.only(left=20, right=20),
                on_hover=self.on_change_bgcolor,
            )
        if ui["type"] == "bool":
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(value=ui["display"], size=16),
                        ft.Switch(
                            value=self.controller.values.value.get(ui["name"], False),
                            on_change=lambda e: [
                                self.controller.update_value(ui["name"], e.control.value),
                                self._on_change(e),
                            ],
                            disabled=not (ui["enable"]),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.only(left=20, right=20),
                on_hover=self.on_change_bgcolor,
            )
        else:  # text
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(value=ui["display"], size=16),
                        ft.TextField(
                            width=200,
                            value=self.controller.values.value.get(ui["name"]),
                            on_change=lambda e: [
                                self.controller.update_value(ui["name"], e.control.value),
                                self._on_change(e),
                            ],
                            disabled=not (ui["enable"]),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.only(left=20, right=20),
                on_hover=self.on_change_bgcolor,
            )

    @obx
    def display_setting_list(self):
        # print("AppSettingPage:display_setting_list")
        return ft.Column(
            [self.display_setting_item(ui) for ui in self.controller.setting_ui.value],
            scroll=ft.ScrollMode.ALWAYS,
            expand=True,
        )

    def build(self):
        """Method that build PackageOptionPage content"""
        # print("AppSettingPage:build")

        return ft.Column(
            [
                ft.TextButton(
                    content=ft.Text("System Setting", size=20),
                    on_click=lambda e: self._on_title_click(),
                ),
                ft.Divider(),
                self.display_setting_list(),
                ft.Divider(),
                ft.Row(
                    [
                        ft.ElevatedButton("Reset", on_click=lambda e: [self.controller.reset(), self._on_change(e)]),
                        ft.ElevatedButton(
                            "Save", on_click=lambda e: [self.controller.save(), self._on_click_save(e)], disabled=True
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=1,
        )
