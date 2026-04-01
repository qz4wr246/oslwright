"""
PackageSelect Page.
"""

import os
from typing import Optional, List
from difflib import get_close_matches

import flet as ft
from fletx.core import FletXPage
from fletx.decorators import obx
from fletx.utils import get_logger, get_page
from ..controllers.package_select_controller import PackageSelectController
from ..models.package_model import PackageModel
from ..models.platform_reason_model import ReasonCode

PKG_CTRL_INDEX = 4

app_booting = True


class PackageSelectPage(FletXPage):
    """PackageSelect Page"""

    def __init__(self):
        # print("PackageSelectPage:__init__")
        super().__init__()
        self.controller = PackageSelectController()
        self.on_init_count = 0
        self.scroll_pos = 0

    def on_init(self):
        # print("PackageSelectPage:on_init")
        self.on_init_count += 1
        if self.on_init_count == 2:
            reason = self.controller.platform_reason.value
            if reason.code == ReasonCode.MISSING_VISUALSTUDIO:
                self.dlg_modal_vc = ft.AlertDialog(
                    modal=True,
                    title=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.WARNING, color=ft.Colors.PRIMARY),
                            ft.Text("Alert"),
                        ],
                        tight=True,
                        spacing=10,
                    ),
                    content=ft.Text("Please Install Visual Studio.\n and restart this application."),
                    actions=[
                        ft.TextButton("Exit", on_click=lambda e: [e.page.close(self.dlg_modal_vc), self.do_exit()]),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                self.page_instance.open(self.dlg_modal_vc)
            elif reason.code == ReasonCode.MISSING_BASE_TOOLS:
                self.dlg_modal_bt = ft.AlertDialog(
                    modal=True,
                    title=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.WARNING, color=ft.Colors.PRIMARY),
                            ft.Text("Alert"),
                        ],
                        tight=True,
                        spacing=10,
                    ),
                    content=ft.Text(
                        f"Please install the following missing tools.\n and restart this application.\n\n{reason.message}\n"
                    ),
                    actions=[
                        ft.TextButton("Exit", on_click=lambda e: [e.page.close(self.dlg_modal_bt), self.do_exit()]),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                self.page_instance.open(self.dlg_modal_bt)

            elif reason.code == ReasonCode.MISSING_EMBEDDED_TOOLS:
                self.dlg_modal_et = ft.AlertDialog(
                    modal=True,
                    title=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.WARNING, color=ft.Colors.PRIMARY),
                            ft.Text("Alert"),
                        ],
                        tight=True,
                        spacing=10,
                    ),
                    content=ft.Text(
                        f"The following tools are not installed.\n\n{reason.message}\n Please press the install tools button.\n"
                    ),
                    actions=[
                        ft.TextButton(
                            "Install tools and exit",
                            on_click=lambda e: [e.page.close(self.dlg_modal_et), self.do_install_tools()],
                        ),
                        ft.TextButton("Exit", on_click=lambda e: [e.page.close(self.dlg_modal_et), self.do_exit()]),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                self.page_instance.open(self.dlg_modal_et)
            self.update_state()

    def on_destroy(self):
        # print("PackageSelectPage:on_destory")
        pass

    def on_change_bgcolor(self, e):
        e.control.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST if e.data == "true" else ft.ColorScheme.background
        e.control.update()

    def do_exit(self):
        os._exit(0)

    def on_select_all(self, value):
        """
        checkboxの更新で、reactive を使用すると、とてつもなく長い遅延が発生する。
        トリッキーであるが直接にCheckBoxの値を更新する。
        """
        for ctrl in self.content.controls[PKG_CTRL_INDEX].widget.controls:
            ctrl.widget.content.controls[0].controls[0].value = value
        self.refresh()

    def on_change_ckeckbox(self, value):
        n_ctrl = len(self.content.controls[PKG_CTRL_INDEX].widget.controls)
        true_cnt = 0
        for ctrl in self.content.controls[PKG_CTRL_INDEX].widget.controls:
            if ctrl.widget.content.controls[0].controls[0].value:
                true_cnt += 1
        self.content.controls[PKG_CTRL_INDEX - 2].controls[0].value = True if n_ctrl == true_cnt else False

        self.refresh()

    def on_scroll_package_list(self, e):
        self.scroll_pos = e.pixels

    def on_submit_search_box(self, e):
        search_query = e.data
        if not search_query:
            return

        keywords = [
            ctrl.widget.content.controls[0].controls[0].label.value
            for ctrl in self.content.controls[PKG_CTRL_INDEX].widget.controls
        ]
        lower_query = search_query.lower()

        # まず部分一致を抽出
        partial = [w for w in keywords if lower_query in w.lower()]
        mapping = {word.lower(): word for word in partial}
        # さらに類似度で並べ替え
        matches = get_close_matches(lower_query, [w.lower() for w in partial], n=5, cutoff=0.1)

        # 元の単語に戻す
        result = [mapping[m] for m in matches if m in mapping]

        if result:
            target_key = result[0]
            # 指定したkeyの位置までスクロール
            # self.content.controls[PKG_CTRL_INDEX].widget.scroll_to(key=target_key, duration=0)
            self.item_height = 40
            for i, c in enumerate(self.content.controls[PKG_CTRL_INDEX].widget.controls):
                if c.key == target_key:
                    pos = i * self.item_height  # item_height は固定値
                    self.content.controls[PKG_CTRL_INDEX].widget.scroll_to(offset=pos)
                    self.page.update()
                    break
            self.refresh()

    def get_selected_packages_name(self):
        names = []
        for ctrl in self.content.controls[PKG_CTRL_INDEX].widget.controls:
            if ctrl.widget.content.controls[0].controls[0].value:
                names.append(ctrl.widget.content.controls[0].controls[0].data)
        return names

    def open_info(self, package: PackageModel):
        self.save_state()
        self.controller.open_info(package)

    def open_option(self, package: PackageModel):
        self.save_state()
        self.controller.open_option(package)

    def open_build(self, package: PackageModel):
        self.save_state()
        self.controller.open_build(package)

    def open_app_setting(self):
        self.save_state()
        self.controller.open_app_setting()

    def open_build_all(self, names: List[str]):
        self.save_state()
        self.controller.build_all(names)

    def save_state(self):
        self.page.client_storage.set("package_list_scroll_pos", self.scroll_pos)
        controls = self.content.controls[PKG_CTRL_INDEX].widget.controls
        checked_idx = [0] * len(controls)
        for idx, ctrl in enumerate(controls):
            value = ctrl.widget.content.controls[0].controls[0].value
            checked_idx[idx] = value
        self.page.client_storage.set("package_list_checked", checked_idx)

        all_check = self.content.controls[PKG_CTRL_INDEX - 2].controls[0].value
        self.page.client_storage.set("package_list_all_check", all_check)

    def update_state(self):
        global app_booting
        if app_booting:
            app_booting = False
            self.page.client_storage.clear()

        checked_idx = self.page.client_storage.get("package_list_checked")
        if checked_idx:
            for idx, ctrl in enumerate(self.content.controls[PKG_CTRL_INDEX].widget.controls):
                ctrl.widget.content.controls[0].controls[0].value = checked_idx[idx]

        pos = self.page.client_storage.get("package_list_scroll_pos")
        if pos:
            self.content.controls[PKG_CTRL_INDEX].widget.scroll_to(offset=pos, duration=0)
        all_check = self.page.client_storage.get("package_list_all_check")
        if all_check:
            self.content.controls[PKG_CTRL_INDEX - 2].controls[0].value = all_check
        self.refresh()

    def do_install_tools(self):
        self.controller.install_tools()
        os._exit(0)

    def build_app_bar(self) -> Optional[ft.AppBar]:
        return ft.AppBar(title=ft.Text("Package Select"), bgcolor=ft.Colors.SURFACE)

    # パッケージアイテム
    @obx
    def display_package_item(self, package: PackageModel):
        # print("PackageSelectPage:display_package_item")
        return ft.Container(
            key=package.display,
            on_hover=self.on_change_bgcolor,
            padding=ft.padding.only(right=10),
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
                                on_change=lambda e: self.on_change_ckeckbox(e.control.value),
                                data=package.name,
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
                                on_click=lambda e, p=package: self.open_info(p),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SETTINGS_ROUNDED,
                                tooltip="Optoin",
                                on_click=lambda e, p=package: self.open_option(p),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CONSTRUCTION_ROUNDED,
                                tooltip="Build",
                                on_click=lambda e, p=package: self.open_build(p),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                ]
            ),
        )

    @obx
    def display_packge_list(self):
        # # print("PackageSelectPage:display_packge_list")
        return ft.ListView(
            controls=[self.display_package_item(p) for p in self.controller.packages.value],
            auto_scroll=False,
            expand=True,
            on_scroll=self.on_scroll_package_list,
        )

    def build(self):
        # print("PackageSelectPage:build")
        return ft.Column(
            [
                ft.Text(f"Select Target Packages", size=20),
                ft.Divider(),
                # 上部操作バー
                ft.Row(
                    [
                        ft.Checkbox(
                            label="Select All",
                            on_change=lambda e: self.on_select_all(e.control.value),
                        ),
                        ft.Container(
                            content=ft.SearchBar(
                                bar_hint_text="Search...", on_submit=lambda e: self.on_submit_search_box(e)
                            ),
                            width=240,
                            height=28,
                        ),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton(
                                    "Reload", icon=ft.Icons.REFRESH, on_click=lambda e: self.controller.reload()
                                ),
                                ft.ElevatedButton(
                                    "Setting",
                                    icon=ft.Icons.SETTINGS_ROUNDED,
                                    on_click=lambda e: self.open_app_setting(),
                                ),
                                ft.ElevatedButton(
                                    "Build All",
                                    icon=ft.Icons.CONSTRUCTION,
                                    on_click=lambda e: self.open_build_all(names=self.get_selected_packages_name()),
                                ),
                            ]
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(),
                self.display_packge_list(),
            ],
            spacing=1,
            expand=True,
        )
