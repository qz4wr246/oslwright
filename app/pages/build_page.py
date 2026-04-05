"""
Build Page.
"""

import flet as ft
from fletx.core import FletXPage
from fletx.decorators import obx
from fletx.navigation import go_back

from ..models.package_model import PackageModel
from ..controllers.build_controller import BuildController
from ..services.build_service import Reason


class BuildPage(FletXPage):
    """Build Page"""

    def __init__(self):
        # print("BuildPage:__init__")
        super().__init__()
        self.controller = BuildController()
        self.initialized = False
        self.init_count = 0

    def on_init(self):
        """Hook called when BuildPage is initialized"""
        # print("BuildPage:on_init")
        self.init_count += 1
        if self.init_count > 1 and not self.initialized:
            routing_param_data = self.route_info.data
            packages: list[PackageModel] = routing_param_data.get("packages", [])
            build_force = routing_param_data.get("build_force", False)
            self.controller.set_build_packages(packages, build_force)
            self.controller.start_build()
            self.initialized = True
            self.modal_dialog = None
            self.controller.on_local("build_finished", self.on_build_finished)

    def on_destroy(self):
        """Hook called when BuildPage will be unmounted."""
        # print("BuildPage:on_destroy")
        pass

    def on_build_finished(self, event):
        def _close_dialog(e):
            if self.modal_dialog:
                e.control.page.close(self.modal_dialog)
            self.modal_dialog = None
            self.refresh()

        reason = event.data
        if reason == Reason.COMPLETED:
            self.modal_dialog = ft.AlertDialog(
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
                    ft.TextButton("Close", on_click=_close_dialog),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page_instance.open(self.modal_dialog)

        elif reason == Reason.USER_INTERRUPTED:
            self.modal_dialog = ft.AlertDialog(
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
                actions=[ft.TextButton("Close", on_click=_close_dialog)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page_instance.open(self.modal_dialog)
        else:
            self.modal_dialog = ft.AlertDialog(
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
                actions=[ft.TextButton("Close", on_click=_close_dialog)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page_instance.open(self.modal_dialog)
        # [stop build] button
        self.content.controls[4].disabled = True

    def _on_title_click(self):
        if not self.controller.is_running:
            go_back()

    def _on_stop_build(self, e):
        def _close_dialog(e):
            e.control.page.close(self.modal_dialog)
            self.modal_dialog = None
            self.refresh()

        self.modal_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(controls=[ft.Icon(name=ft.Icons.WARNING_ROUNDED), ft.Text("Confimination")]),
            content=ft.Text("Do you want to stop the build?"),
            actions=[
                ft.TextButton("Yes", on_click=lambda e: [_close_dialog(e), self.controller.stop_build()]),
                ft.TextButton("No", on_click=_close_dialog),
            ],
        )
        self.page_instance.open(self.modal_dialog)

    @obx
    def build_status_display(self):
        # print("BuildPage:build_status_display")
        return ft.Row(
            controls=[
                ft.Container(
                    margin=20,
                    alignment=ft.alignment.center,
                    content=ft.Stack(
                        [
                            ft.ProgressRing(
                                width=130,
                                height=130,
                                stroke_width=10,
                                stroke_cap=ft.StrokeCap.ROUND,
                                bgcolor=ft.Colors.BLUE_GREY_700,
                                value=self.controller.progress.value,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    f"{self.controller.tx_remaining_time.value}",
                                    weight=ft.FontWeight.BOLD,
                                    size=24,
                                    color=self.controller.tx_remaining_time_color.value,
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
                        ft.DataColumn(ft.Text("START TIME:")),
                        ft.DataColumn(ft.Text(self.controller.tx_start_time.value)),
                    ],
                    rows=[
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text("COMPLETION TIME:")),
                                ft.DataCell(ft.Text(self.controller.tx_completion_time.value)),
                            ],
                        ),
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text("ELAPSED TIME:")),
                                ft.DataCell(ft.Text(self.controller.tx_elapsed_time.value)),
                            ],
                        ),
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text("PROCESSED:")),
                                ft.DataCell(ft.Text(self.controller.tx_processed.value)),
                            ],
                        ),
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text("STAGE:")),
                                ft.DataCell(ft.Text(self.controller.tx_status.value)),
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

    @obx
    def logs_display(self):
        return ft.ListView(
            controls=[
                ft.Text(value=line.text, color=line.color, selectable=True) for line in self.controller.logs.value
            ],
            expand=True,
            spacing=2,
            auto_scroll=True,
        )

    def build(self):
        # print("BuildPage:build")
        return ft.Column(
            controls=[
                ft.TextButton(
                    content=ft.Text("Build Packages", size=20),
                    on_click=lambda e: self._on_title_click(),
                ),
                ft.Divider(),
                self.build_status_display(),
                ft.Divider(),
                ft.ElevatedButton(
                    "Stop Build",
                    on_click=lambda e: self._on_stop_build(e),
                    icon=ft.Icons.STOP_CIRCLE_OUTLINED,
                ),
                ft.Divider(),
                self.logs_display(),
            ],
            expand=True,
        )
