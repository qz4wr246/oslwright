from typing import Any

import flet as ft

from oslwright.ow_package import Package
from oslwright.ow_platform import Platform
from oslwright.ui_settings import uiSettingItem


class uiDefaultSettings(ft.Column):

    def __init__(self, platform: Platform, packages):
        super().__init__()
        self.platform = platform
        self.packages = packages
        self.params = [
            {
                "display": "Build arch",
                "name": "build_arch_default",
                "type": "chose",
                "item": ["x64", "x32"],
                "default": platform.build_arch_default,
            },
            {
                "display": "MSVC toolset version",
                "name": "msvc_toolset_version_default",
                "type": "chose",
                "item": platform.msvc_toolset_versions,
                "default": platform.msvc_toolset_version_default,
            },
            {
                "display": "MSVC runtime library",
                "name": "msvc_runtime_library_default",
                "type": "chose",
                "item": ["mt", "md"],
                "default": platform.msvc_runtime_library_default,
            },
            {
                "display": "Build library",
                "name": "build_library_default",
                "type": "chose",
                "item": ["shared", "static"],
                "default": platform.build_library_default,
            },
            {
                "display": "Using CUDA",
                "name": "cuda_enable_default",
                "enable": True if platform.cuda_versions else False,
                "type": "bool",
                "default": platform.cuda_enable_default,
            },
            {
                "display": "CUDA Version",
                "name": "cuda_version_default",
                "enable": "cuda_enable_default",
                "type": "chose",
                "item": platform.cuda_versions,
                "default": platform.cuda_version_default,
            },
        ]
        self.settings: dict = {
            "build_arch_default": platform.build_arch_default,
            "msvc_toolset_version_default": platform.msvc_toolset_version_default,
            "msvc_runtime_library_default": platform.msvc_runtime_library_default,
            "build_library_default": platform.build_library_default,
            "cuda_enable_default": platform.cuda_enable_default,
            "cuda_version_default": platform.cuda_version_default,
        }

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

        for key, value in self.settings.items():
            setattr(self.platform, key, value)

        self.platform.SaveDefaultSetting()
        for package in self.packages:
            package.Reload()
        e.page.go("/")


class uiDefaultSettingsView(ft.View):

    def __init__(self, param):
        platform, packages = param
        controls = [
            ft.AppBar(title=ft.Text(f"Default Settings"), bgcolor=ft.colors.SURFACE_VARIANT),
            uiDefaultSettings(platform, packages),
        ]
        super().__init__("/default_settings", controls=controls)
