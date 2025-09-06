from typing import Any

import flet as ft

from oslwright.ow_package import Package


class uiSettingItem(ft.Container):

    def __init__(self, param: dict, settings: dict, on_change: Any | None = None):
        super().__init__()
        self.on_change = on_change
        self.param: dict = param
        self.settings: dict = settings
        default_val = (
            self.settings[self.param["name"]] if self.param["name"] in self.settings else self.param["default"]
        )

        if self.param["type"] == "bool":
            self.value_control = ft.CupertinoSwitch(value=bool(default_val), on_change=self.on_value_changed)
        elif self.param["type"] == "string":
            self.value_control = ft.TextField(value=default_val, on_change=self.on_value_changed)
        elif self.param["type"] == "chose":
            self.value_control = ft.Dropdown(
                value=default_val,
                options=[ft.dropdown.Option(i) for i in self.param["item"]],
                on_change=self.on_value_changed,
                width=200,
                content_padding=ft.Padding(16, 1, 16, 1),
                label_style=ft.TextStyle(size=16),
                text_style=ft.TextStyle(size=16),
            )

        self.content = ft.Row(
            controls=[ft.Text(value=self.param["display"], size=16), self.value_control],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.padding = ft.padding.only(left=20, right=20)
        self.on_hover = self.on_change_bgcolor
        self.update_disabled()

    def on_change_bgcolor(self, e):
        e.control.bgcolor = ft.colors.SURFACE_VARIANT if e.data == "true" else ft.colors.SURFACE
        e.control.update()

    def update_disabled(self):
        disabled = (
            (
                not bool(self.settings[self.param["enable"]])
                if isinstance(self.param["enable"], str)
                else not bool(self.param["enable"])
            )
            if "enable" in self.param
            else False
        )
        self.value_control.disabled = disabled
        # self.update()

    def on_value_changed(self, e):
        self.settings[self.param["name"]] = self.value_control.value
        self.on_change(e)


class uiSettings(ft.Column):

    def __init__(self, package: Package):
        super().__init__()
        self.package = package
        self.settings = self.package.GetSettings()
        self.params = self.package.GetSettingParam()
        self.setting_list = ft.Column(expand=True, scroll=ft.ScrollMode.ALWAYS)

        self.save_button = ft.ElevatedButton("Save", icon=ft.icons.DRAW, on_click=self.on_save_settings, disabled=True)
        for param in self.params:
            self.setting_list.controls.append(
                uiSettingItem(param=param, settings=self.settings, on_change=self.on_change_value)
            )
        self.controls = [
            self.setting_list,
            ft.Divider(),
            ft.Row(controls=[self.save_button], alignment=ft.MainAxisAlignment.END),
        ]
        self.expand = True

    def on_change_value(self, e):
        for item in self.setting_list.controls:
            item.update_disabled()

        self.save_button.disabled = False
        self.update()

    def on_save_settings(self, e):
        self.save_button.disabled = True
        self.package.SetSettings(self.settings)
        e.page.go("/")


class uiSettingsView(ft.View):

    def __init__(self, package: Package):
        controls = [
            ft.AppBar(title=ft.Text(f"Settings : {package.display}"), bgcolor=ft.colors.SURFACE_VARIANT),
            uiSettings(package),
        ]
        super().__init__("/settings", controls=controls)
