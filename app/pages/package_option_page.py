"""
PackageOption Page.
"""

import flet as ft

from ..core.constants import Routes
from ..controllers.package_option_controller import PackageOptionController
from ..models.package_model import PackageModel
from ..models.package_option_ui_model import OptionUiItem


@ft.component
def PackageOptionPage():
    """PackageInfo Page"""
    page = ft.context.page

    packages = page.session.store.get("packages")
    package = packages[0]

    controller = ft.use_memo(lambda: PackageOptionController(), [])

    is_loaded, set_is_loaded = ft.use_state(False)
    if not is_loaded:
        controller.load_option(package)
        set_is_loaded(True)

    save_button_disabled, set_save_button_disabled = ft.use_state(True)

    def on_revert_selected(e):
        ret = controller.revert(e.control.data)
        set_save_button_disabled(not ret)

    def on_save_click(e):
        controller.save()
        set_save_button_disabled(True)

    def on_reset_click(e):
        controller.reset()
        set_save_button_disabled(False)

    def on_change(e):
        set_save_button_disabled(False)
        controller.update_value(e.control.data, e.control.value)

    save_button = ft.Button(content="Save", disabled=save_button_disabled, on_click=on_save_click)

    def OptionItem(ui: OptionUiItem):
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
            # OptionItem List
            ft.Column(
                controls=[OptionItem(ui) for ui in controller.option_ui],
                auto_scroll=False,
                scroll=ft.ScrollMode.ALWAYS,
                expand=True,
                spacing=10,
            ),
            ft.Divider(),
            ft.Row(
                controls=[
                    ft.PopupMenuButton(
                        content=ft.Button(
                            content="Revert to...",
                            icon=ft.Icons.ARROW_DROP_DOWN,
                            disabled=True,
                            style=ft.ButtonStyle(
                                color={ft.ControlState.DEFAULT: ft.Colors.PRIMARY},
                                shape=ft.StadiumBorder(),
                            ),
                        ),
                        items=[
                            ft.PopupMenuItem(
                                content=ft.Text("Download"),
                                data="download",
                                on_click=on_revert_selected,
                            ),
                            ft.PopupMenuItem(
                                content=ft.Text("Configure"),
                                data="configure",
                                on_click=on_revert_selected,
                            ),
                            ft.PopupMenuItem(
                                content=ft.Text("Build"),
                                data="build",
                                on_click=on_revert_selected,
                            ),
                            ft.PopupMenuItem(
                                content=ft.Text("Install"),
                                data="install",
                                on_click=on_revert_selected,
                            ),
                        ],
                        tooltip="",
                    ),
                    ft.Row(
                        controls=[ft.Button("Reset", on_click=on_reset_click), save_button],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        ],
        spacing=1,
        expand=True,
    )
    return ft.View(
        key="PackageOptionPage",
        route=Routes.PKG_OPTION,
        appbar=ft.AppBar(
            title=ft.Text(f"Package Option: {package.display}"),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: e.page.navigate(Routes.HOME)),
        ),
        controls=[layout],
    )
