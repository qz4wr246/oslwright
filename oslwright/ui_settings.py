from typing import Any

import flet as ft

from oslwright.ow_package import Package


class uiSettingItem(ft.Container):

    def __init__(self, param: dict, settings: dict, on_change: Any | None = None):
        super().__init__()
        self.on_change = on_change
        self.param: dict = param
        self.settings: dict = settings
        setting_val = (
            self.settings[self.param["name"]] if self.param["name"] in self.settings else self.param["default"]
        )

        if self.param["type"] == "bool":
            self.value_control = ft.CupertinoSwitch(value=bool(setting_val), on_change=self.on_value_changed)
            self.default = bool(self.param["default"])
        elif self.param["type"] == "string":
            self.value_control = ft.TextField(value=setting_val, on_change=self.on_value_changed)
            self.default = self.param["default"]
        elif self.param["type"] == "chose":
            self.value_control = ft.Dropdown(
                value=setting_val,
                options=[ft.dropdown.Option(i) for i in self.param["item"]],
                on_change=self.on_value_changed,
                width=200,
                content_padding=ft.Padding(16, 1, 16, 1),
                label_style=ft.TextStyle(size=16),
                text_style=ft.TextStyle(size=16),
            )
            self.default = self.param["default"]
        else:
            self.default = self.param["default"]

        self.content = ft.Row(
            controls=[ft.Text(value=self.param["display"], size=16), self.value_control],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.padding = ft.padding.only(left=20, right=20)
        self.on_hover = self.on_change_bgcolor
        self.update_disabled()

    def on_change_bgcolor(self, e):
        e.control.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST if e.data == "true" else ft.Colors.SURFACE
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

    def on_value_changed(self, e):
        self.settings[self.param["name"]] = self.value_control.value
        self.on_change(e)

    def reset(self):
        self.settings[self.param["name"]] = self.default
        self.value_control.value = self.default


class uiSettings(ft.Column):

    def __init__(self, package: Package):
        super().__init__()
        self.package = package
        self.settings = self.package.GetSettings()
        self.params = self.package.GetSettingParam()
        self.setting_list = ft.Column(expand=True, scroll=ft.ScrollMode.ALWAYS)

        self.save_button = ft.ElevatedButton("Save", icon=ft.Icons.DRAW, on_click=self.on_save_settings, disabled=True)
        self.reset_button = ft.ElevatedButton(
            "Rest", icon=ft.Icons.SETTINGS_BACKUP_RESTORE, on_click=self.on_reset_settings, disabled=True
        )
        for param in self.params:
            self.setting_list.controls.append(
                uiSettingItem(param=param, settings=self.settings, on_change=self.on_change_value)
            )
        self.controls = [
            self.setting_list,
            ft.Divider(),
            ft.Row(controls=[self.reset_button, self.save_button], alignment=ft.MainAxisAlignment.END),
        ]
        self.expand = True

    def on_change_value(self, e):
        for item in self.setting_list.controls:
            item.update_disabled()

        self.save_button.disabled = False
        self.reset_button.disabled = False
        self.update()

    def on_save_settings(self, e):
        self.save_button.disabled = True
        self.package.SetSettings(self.settings)
        e.page.go("/")

    def on_reset_settings(self, e):
        for item in self.setting_list.controls:
            item.reset()
        self.reset_button.disabled = True
        self.update()


class uiSettingsView(ft.View):

    def __init__(self, package: Package):
        controls = [
            ft.AppBar(title=ft.Text(f"Settings : {package.display}"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST),
            uiSettings(package),
        ]
        super().__init__("/settings", controls=controls)
