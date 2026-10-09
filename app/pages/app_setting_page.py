"""
AppSetting Page.
"""

from typing import Any, Dict

import flet as ft

from ..models.package_option_ui_model import OptionUiItem
from ..controllers.app_setting_controller import AppSettingController
from ..core.constants import Routes


@ft.component
def AppSettingPage():
    """AppSetting Page"""

    controller = ft.use_memo(lambda: AppSettingController(), [])

    is_loaded, set_is_loaded = ft.use_state(False)
    if not is_loaded:
        controller.load_setting()
        set_is_loaded(True)

    save_button_disabled, set_save_button_disabled = ft.use_state(True)

    def on_save_click(e):
        controller.save()
        set_save_button_disabled(True)

    def on_reset_click(e):
        controller.reset()
        set_save_button_disabled(True)

    def on_change(e):
        set_save_button_disabled(False)
        controller.update_value(e.control.data, e.control.value)

    save_button = ft.Button(content="Save", disabled=save_button_disabled, on_click=on_save_click)

    def SettingItem(ui: OptionUiItem):
        ctrlitem = None
        if ui.type == "choice":
            ctrlitem = ft.Dropdown(
                key=controller.values[ui.name].name,
                width=250,
                value=controller.values[ui.name].value,
                disabled=controller.values[ui.name].disabled,
                options=[ft.dropdown.Option(x) for x in ui.items],
                on_select=on_change,
                data=ui.name,
            )
        elif ui.type == "bool":
            ctrlitem = ft.Switch(
                key=controller.values[ui.name].name,
                value=controller.values[ui.name].value,
                disabled=controller.values[ui.name].disabled,
                on_change=on_change,
                data=ui.name,
            )
        else:  # text
            ctrlitem = ft.TextField(
                key=controller.values[ui.name].name,
                width=250,
                value=controller.values[ui.name].value,
                disabled=controller.values[ui.name].disabled,
                on_change=on_change,
                data=ui.name,
            )

        hover_bgcolor, set_hover_bgcolor = ft.use_state(None)

        def on_hover(e):
            if e.data:
                set_hover_bgcolor(ft.Colors.SURFACE_CONTAINER_HIGHEST)
            else:
                set_hover_bgcolor(None)

        container = ft.Container(
            content=ft.Row(
                controls=[ft.Text(value=ui.display, size=16), ctrlitem],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            key=ui.name,
            padding=ft.padding.Padding.symmetric(horizontal=20),
            on_hover=on_hover,
            bgcolor=hover_bgcolor,
        )
        return container

    layout = ft.Column(
        controls=[
            ft.Column(
                controls=[SettingItem(ui) for ui in controller.setting_ui],
                scroll=ft.ScrollMode.ALWAYS,
                expand=True,
                spacing=10,
            ),
            ft.Divider(),
            ft.Row(
                controls=[ft.Button("Reset", on_click=on_reset_click), save_button],
                alignment=ft.MainAxisAlignment.END,
            ),
        ],
        spacing=1,
        expand=True,
    )
    return ft.View(
        key="AppSettingPage",
        route=Routes.PKG_OPTION,
        appbar=ft.AppBar(
            title=ft.Text(f"System Settings"),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: e.page.navigate(Routes.HOME)),
        ),
        controls=[layout],
    )
