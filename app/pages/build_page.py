"""
app/pages/build_page.py
Build Page.
"""

import flet as ft
from ..core.constants import Routes
from ..controllers.build_controller import BuildController
from ..services.build_service import Reason
from ..models.package_model import PackageModel
from ..models.build_status_model import BuildStatusModel


@ft.component
def BuildPage():
    """Build Page"""
    page = ft.context.page

    # 1. 戻るボタンの無効化状態を管理するStateを追加 (初期値は True = 無効)
    back_disabled, set_back_disabled = ft.use_state(True)
    # build status
    build_status, set_build_status = ft.use_state(BuildStatusModel())

    # チェックボタン
    detail_checked, set_detail_checked = ft.use_state(False)

    def on_build_status(status: BuildStatusModel):
        set_build_status(status)

        if status.reason == Reason.COMPLETED:
            # open Success Dialog
            set_show_success(True)

        elif status.reason == Reason.USER_INTERRUPTED:
            # open Abort Dialog
            set_show_abort(True)

        elif status.reason == Reason.ERROR or status.reason == Reason.EXCEPTION:
            # open Error Dialog
            set_show_error(True)

    controller = ft.use_memo(lambda: BuildController(page, on_build_status), [])

    # Success Dialog
    show_success, set_show_success = ft.use_state(False)
    ft.use_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.PRIMARY),
                    ft.Text("Infomation"),
                ],
                tight=True,
                spacing=10,
            ),
            content=ft.Text("Packages built successfully."),
            actions=[
                ft.TextButton(
                    "Close",
                    on_click=lambda: [
                        set_back_disabled(False),
                        set_show_success(False),
                        build_status.build_force and page.run_task(page.window.close),
                    ],
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if show_success
        else None
    )

    # Abort Dialog
    show_abort, set_show_abort = ft.use_state(False)
    ft.use_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.AMBER),
                    ft.Text("Infomation", color=ft.Colors.AMBER),
                ],
                tight=True,
                spacing=10,
            ),
            content=ft.Text("Package build was aborted by the user."),
            actions=[
                ft.TextButton(
                    "Close",
                    on_click=lambda: [
                        set_back_disabled(False),
                        set_show_abort(False),
                        build_status.build_force and page.run_task(page.window.close),
                    ],
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if show_abort
        else None
    )
    # Error Dialog
    show_error, set_show_error = ft.use_state(False)
    ft.use_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ERROR),
                    ft.Text("Error", color=ft.Colors.ERROR),
                ],
                tight=True,
                spacing=10,
            ),
            content=ft.Text("An error occurred during the package build process."),
            actions=[
                ft.TextButton(
                    "Close",
                    on_click=lambda: [
                        set_back_disabled(False),
                        set_show_error(False),
                        build_status.build_force and page.run_task(page.window.close),
                    ],
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if show_error
        else None
    )

    # Comfirm Dialog
    show_comfirm, set_show_comfirm = ft.use_state(False)
    ft.use_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Row(controls=[ft.Icon(icon=ft.Icons.WARNING_ROUNDED), ft.Text("Confirmination")]),
            content=ft.Text("Do you want to stop the build?"),
            actions=[
                ft.TextButton("Yes", on_click=lambda: [controller.stop_build(), set_show_comfirm(False)]),
                ft.TextButton("No", on_click=lambda: set_show_comfirm(False)),
            ],
        )
        if show_comfirm
        else None
    )

    def on_mount():
        packages = page.session.store.get("packages")
        build_force = bool(page.session.store.get("build_force"))
        controller.set_build_packages(packages, build_force)
        controller.start_build()

    def on_unmount():
        controller.stop_build()

    ft.use_effect(setup=on_mount, dependencies=[], cleanup=on_unmount)

    def on_stop_build(e):
        # open Error Dialog
        set_show_comfirm(True)

    def on_check_detail(e):
        val = e.control.value
        set_detail_checked(val)
        controller.set_log_detai(val)

    build_status_layout = ft.Row(
        controls=[
            ft.Container(
                margin=20,
                alignment=ft.Alignment.CENTER,
                content=ft.Stack(
                    [
                        ft.ProgressRing(
                            width=130,
                            height=130,
                            stroke_width=10,
                            stroke_cap=ft.StrokeCap.ROUND,
                            bgcolor=ft.Colors.BLUE_GREY_700,
                            value=build_status.progress,
                        ),
                        ft.Container(
                            content=ft.Text(
                                f"{build_status.tx_remaining_time}",
                                weight=ft.FontWeight.BOLD,
                                size=24,
                                color=build_status.tx_remaining_time_color,
                            ),
                            alignment=ft.Alignment(0, 0),
                        ),
                    ],
                    width=130,
                    height=130,
                ),
            ),
            ft.DataTable(
                columns=[
                    ft.DataColumn(label=ft.Text("START TIME:")),
                    ft.DataColumn(label=ft.Text(build_status.tx_start_time)),
                ],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("COMPLETION TIME:")),
                            ft.DataCell(ft.Text(build_status.tx_completion_time)),
                        ],
                    ),
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("ELAPSED TIME:")),
                            ft.DataCell(ft.Text(build_status.tx_elapsed_time)),
                        ],
                    ),
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("PROCESSED:")),
                            ft.DataCell(ft.Text(build_status.tx_processed)),
                        ],
                    ),
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("STAGE:")),
                            ft.DataCell(ft.Text(build_status.tx_status)),
                        ],
                    ),
                ],
                heading_row_height=36,
                data_row_min_height=36,
                data_row_max_height=36,
                expand=True,
            ),
        ],
        spacing=20,
    )

    logs_layout = ft.ListView(
        controls=[ft.Text(value=log.text, color=log.color, selectable=True) for log in controller.log_store.list],
        expand=True,
        spacing=2,
        auto_scroll=True,
    )

    layout = ft.Column(
        controls=[
            build_status_layout,
            ft.Divider(),
            ft.Row(
                controls=[
                    ft.Button(
                        "Stop Build",
                        on_click=on_stop_build,
                        icon=ft.Icons.STOP_CIRCLE_OUTLINED,
                    ),
                    ft.Checkbox("Log details", value=detail_checked, on_change=on_check_detail),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            logs_layout,
        ],
        spacing=1,
        expand=True,
    )

    return ft.View(
        key="BuildPage",
        route=Routes.BUILD,
        appbar=ft.AppBar(
            title=ft.Text("Build Packages."),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK, disabled=back_disabled, on_click=lambda e: e.page.navigate(Routes.HOME)
            ),
        ),
        controls=[layout],
    )
