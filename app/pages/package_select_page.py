"""
PackageSelect Page.
"""

from typing import Optional, List, Any
from difflib import get_close_matches
from dataclasses import dataclass

import flet as ft

from ..core.constants import Routes
from ..controllers.package_select_controller import PackageSelectController
from ..models.package_model import PackageModel
from ..models.platform_reason_model import ReasonCode


@ft.component
def PackageItem(package):

    page = ft.context.page

    hover_bgcolor, set_hover_bgcolor = ft.use_state(None)

    def on_hover(e):
        if e.data:
            set_hover_bgcolor(ft.Colors.SURFACE_CONTAINER_HIGHEST)
        else:
            set_hover_bgcolor(None)

    def handle_checkbox_change(e):
        package.selected.value = e.control.value

    def handle_info(e):
        page.session.store.set("packages", [package])
        page.session.store.set("build_force", False)
        page.navigate(Routes.PKG_INFO)

    def handle_option(e):
        page.session.store.set("packages", [package])
        page.session.store.set("build_force", False)
        page.navigate(Routes.PKG_OPTION)

    def handle_build(e):
        page.session.store.set("packages", [package])
        page.session.store.set("build_force", False)
        page.navigate(Routes.BUILD)

    container = ft.Container(
        key=ft.ScrollKey(package.name.lower()),
        padding=ft.padding.Padding.symmetric(horizontal=10),
        on_hover=on_hover,
        bgcolor=hover_bgcolor,
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Checkbox(
                            label=ft.Text(
                                value=package.display,
                                style=ft.TextStyle(size=18),
                                no_wrap=False,  # 折り返しを有効化,
                                width=200,
                            ),
                            value=package.selected.value,
                            on_change=handle_checkbox_change,
                            data=package,
                        )
                    ],
                    width=250,
                ),
                ft.Column(
                    expand=True,
                    spacing=0,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    f"version: {package.latest_version}", theme_style=ft.TextThemeStyle.BODY_MEDIUM
                                ),
                                ft.Text(f"license: {package.license}", theme_style=ft.TextThemeStyle.BODY_MEDIUM),
                            ]
                        ),
                        ft.Text(
                            value=package.description,
                            theme_style=ft.TextThemeStyle.BODY_SMALL,
                            italic=True,
                            max_lines=2,
                            no_wrap=False,
                        ),
                    ],
                ),
                ft.Row(
                    spacing=0,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.INFO_OUTLINE_ROUNDED,
                            tooltip="Infomation",
                            on_click=handle_info,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS_ROUNDED,
                            tooltip="Optoin",
                            on_click=handle_option,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CONSTRUCTION_ROUNDED,
                            tooltip="Build",
                            on_click=handle_build,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
            ]
        ),
    )
    return container


# 【重要】画面が切り替わっても破棄されない、グローバルな状態保持用クラス
class AppState:
    # ホーム画面のスクロール位置を記憶する変数 (初期値は 0.0)
    home_scroll_offset = 0.0


@ft.component
def PackageSelectPage():
    """ """
    page = ft.context.page

    controller = ft.use_memo(lambda: PackageSelectController(), [])
    is_all_selected, set_is_all_selected = ft.use_state(False)
    listview_ref = ft.use_ref()

    def handle_scroll(e):
        # e.pixels から現在のスクロール位置（ピクセル単位）を取得して保存
        AppState.home_scroll_offset = e.pixels

    def on_init():
        page = ft.context.page
        # 画面が戻ってきたときに記憶していた位置へスクロールさせる
        if listview_ref.current and AppState.home_scroll_offset > 0:
            e_page = listview_ref.current.page
            if e_page:
                e_page.run_task(listview_ref.current.scroll_to, offset=AppState.home_scroll_offset, duration=0)

    ft.use_effect(on_init, [])

    package_listview = ft.Column(
        ref=listview_ref,
        controls=[PackageItem(p) for p in controller.packages],
        auto_scroll=False,
        scroll=ft.ScrollMode.ALWAYS,
        expand=True,
        on_scroll=handle_scroll,
    )

    def on_select_all(value):
        if package_listview:
            for pkg in controller.packages:
                pkg.selected.value = value
            set_is_all_selected(value)

    async def on_submit_searchbar(e):
        query = e.data.strip().lower() if e.data else ""

        def search_package(packages: list[PackageModel], query_lower: str) -> str | None:
            matches = [(idx, p.name) for p in packages if (idx := p.display.lower().find(query_lower)) >= 0]
            return min(matches, key=lambda x: x[0])[1] if matches else None

        key = search_package(controller.packages, query)
        if key and listview_ref.current:
            await listview_ref.current.scroll_to(scroll_key=ft.ScrollKey(key.lower()), duration=500)

    def open_reload(e):
        controller.reload()

    def open_app_setting(e):
        e.page.navigate(Routes.APP_SETTING)

    def open_build_all(e):
        selected_packages = [pkg for pkg in controller.packages if pkg.selected is not None and pkg.selected.value]
        page.session.store.set("packages", selected_packages)
        page.session.store.set("build_force", False)
        page.navigate(Routes.BUILD)

    layout = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Checkbox(
                        label="Select All",
                        value=is_all_selected,
                        on_change=lambda e: on_select_all(e.control.value),
                    ),
                    ft.Container(
                        content=ft.SearchBar(
                            bar_hint_text="Search...",
                            on_submit=on_submit_searchbar,
                        ),
                        width=240,
                        height=28,
                    ),
                    ft.Row(
                        controls=[
                            ft.Button(
                                content="Reload",
                                icon=ft.Icons.REFRESH,
                                on_click=open_reload,
                            ),
                            ft.Button(
                                content="Setting",
                                icon=ft.Icons.SETTINGS_ROUNDED,
                                on_click=open_app_setting,
                            ),
                            ft.Button(
                                content="Build All",
                                icon=ft.Icons.CONSTRUCTION,
                                on_click=open_build_all,
                            ),
                        ],
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            package_listview,
        ],
        spacing=1,
        expand=True,
    )
    return ft.View(
        route=Routes.HOME,
        appbar=ft.AppBar(
            title=ft.Text(f"Select Target Packages", size=20), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
        ),
        controls=[layout],
    )
