import asyncio
import datetime
import logging
import os

import flet as ft

from oslwright.ow_package import Package
from oslwright.ow_utils import Post


class uiBuild(ft.Column):
    def __init__(self, target_packages: list[Package], auto_exit: bool):
        super().__init__()
        self.task_lock = asyncio.Lock()

        self.running = False
        self.auto_exit = auto_exit
        plat = target_packages[0].platform
        self.build_packages = plat.GetTargetPackages(target_packages)
        total_time = 0
        for bld_pkg in self.build_packages:
            total_time += bld_pkg["package"].process_time
        self.start_time = None
        self.total_process_time = total_time
        self.remaining_time = total_time
        self.n_builded = 0

        self.progress_ring = ft.ProgressRing(
            width=120,
            height=120,
            stroke_width=10,
            stroke_cap=ft.StrokeCap.ROUND,
            value=0,
            bgcolor=ft.Colors.BLUE_GREY_700,
        )
        self.tx_remaining_time = ft.Text("00:00:00", weight=ft.FontWeight.BOLD, size=24)

        stack = ft.Stack(
            [self.progress_ring, ft.Container(content=self.tx_remaining_time, alignment=ft.Alignment(0, 0))],
            width=120,
            height=120,
        )

        self.tx_start_time = ft.Text()
        self.tx_prediction_time = ft.Text()
        self.tx_elapsed_time = ft.Text()
        self.tx_build_project = ft.Text()
        self.tx_status = ft.Text()

        data_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text("START TIME:")), ft.DataColumn(self.tx_start_time)],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("PREDICTION TIME:")),
                        ft.DataCell(self.tx_prediction_time),
                    ],
                ),
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("ELAPSED TIME:")),
                        ft.DataCell(self.tx_elapsed_time),
                    ],
                ),
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("PROJECT:")),
                        ft.DataCell(self.tx_build_project),
                    ],
                ),
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("STATUS:")),
                        ft.DataCell(self.tx_status),
                    ],
                ),
            ],
            heading_row_height=36,
            data_row_min_height=36,
            data_row_max_height=36,
            expand=True,
        )
        self.btn_stop = ft.ElevatedButton("Stop build", icon=ft.Icons.STOP_CIRCLE_OUTLINED, on_click=self.on_stop_build)
        self.progress_area = ft.Column(
            controls=[
                ft.Row(controls=[ft.Container(stack, width=180, alignment=ft.Alignment(0, 0)), data_table]),
                ft.Row(controls=[self.btn_stop], alignment=ft.MainAxisAlignment.END),
            ]
        )

        self.output_area = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=1, width=float("inf"))
        self.output_area.expand = True

        self.controls = [
            self.progress_area,
            ft.Divider(),
            self.output_area,
        ]
        self.expand = True
        self.verbose = False

    def did_mount(self):
        self.running = True
        self.elapsed_time = 0
        self.start_time = datetime.datetime.now()
        self.tx_start_time.value = f"{self.start_time.strftime('%Y/%m/%d %H:%M:%S')}"
        self.prediction_time = self.start_time + datetime.timedelta(seconds=self.total_process_time)
        self.tx_prediction_time.value = f"{self.prediction_time.strftime('%Y/%m/%d %H:%M:%S')}"

        Post.SetHandler(
            info_handler=self.put_info,
            debug_handler=self.put_debug,
            error_handler=self.put_error,
            status_handler=self.put_status,
        )
        self.page.run_task(self.update_timer)
        self.page.run_task(self.do_build_packages)

    def will_unmount(self):
        self.running = False
        Post.SetHandler(
            info_handler=None,
            debug_handler=None,
            error_handler=None,
            status_handler=None,
        )

    async def update_timer(self):
        while self.running:
            hours, remainder = divmod(self.elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            etime = "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
            self.tx_elapsed_time.value = f"{etime}"

            hours, remainder = divmod(self.remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            rtime = "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
            self.tx_remaining_time.value = rtime

            if self.total_process_time > 0:
                self.progress_ring.value = self.elapsed_time / self.total_process_time
            else:
                self.progress_ring.value = 1.0

            self.tx_build_project.value = f"{self.n_builded} / {len(self.build_packages)}"

            self.tx_prediction_time.value = f"{self.prediction_time.strftime('%Y/%m/%d %H:%M:%S')}"
            self.update()

            await asyncio.sleep(1)
            self.elapsed_time += 1
            self.remaining_time -= 1

    def on_stop_build(self, e):

        def on_click_no(e):
            self.page.close(dlg_modal)

        def on_click_yes(e):
            self.btn_stop.disabled = True
            self.btn_stop.update()
            self.page.close(dlg_modal)
            self.tx_status.value = "Stopping build"
            self.tx_status.update()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.stop_task())

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Row(controls=[ft.Icon(name=ft.Icons.WARNING_ROUNDED), ft.Text("Confimination")]),
            content=ft.Text("Do you want to stop the build?"),
            actions=[
                ft.TextButton("Yes", on_click=on_click_yes),
                ft.TextButton("No", on_click=on_click_no),
            ],
        )
        self.page.open(dlg_modal)
        self.page.update()

    async def stop_task(self):
        async with self.task_lock:
            if self.current_package:
                self.current_package.StopBuild()
            self.running = False

    async def do_build_packages(self):
        reason = Package.Reaseon.COMPLETED
        for bld_pkg in self.build_packages:
            async with self.task_lock:
                if self.running:
                    self.current_package = bld_pkg["package"]
                else:
                    reason = Package.Reaseon.USER_INTERRUPTED
                    self.current_package = None
                    break

            start_time = datetime.datetime.now()

            reason = bld_pkg["package"].RunStages(bld_pkg["settings"])

            end_time = datetime.datetime.now()
            sec = abs(end_time - start_time).total_seconds()
            dlt = bld_pkg["package"].process_time - sec
            self.total_process_time -= dlt
            self.remaining_time -= dlt
            self.n_builded += 1
            self.prediction_time = start_time + datetime.timedelta(seconds=self.total_process_time)

            if reason != Package.Reaseon.COMPLETED:
                break

        title = ft.Row(controls=[ft.Icon(name=ft.Icons.INFO_OUTLINE), ft.Text("Infomation")])
        message = ft.Text("Packages build completed.")
        if reason == Package.Reaseon.ERROR:
            title = ft.Row(controls=[ft.Icon(name=ft.Icons.WARNING_ROUNDED), ft.Text("Error")])
            message = ft.Text(f"Build error in {bld_pkg["package"].name}.")

        elif reason == Package.Reaseon.USER_INTERRUPTED:
            title = ft.Row(controls=[ft.Icon(name=ft.Icons.INFO_OUTLINE), ft.Text("Infomation")])
            message = ft.Text(f"Stop build in {bld_pkg["package"].name}.")

        def close_dlg(e):
            self.page.close(dlg_modal)
            if self.auto_exit:
                self.page.window.destroy()
            else:
                self.page.go("/")

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=title,
            content=message,
            actions=[
                ft.TextButton("Close", on_click=lambda e: close_dlg(e)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        await asyncio.sleep(1)
        self.btn_stop.disabled = False
        self.running = False
        self.page.open(dlg_modal)
        self.page.update()

    def put_info(self, message: str):
        message = message.rstrip("\n")
        logging.info(message)
        self.output_area.controls.append(ft.Text(value=message, selectable=True))
        self.output_area.scroll_to(offset=-1)

    def put_debug(self, message: str):
        message = message.rstrip("\n")
        logging.info(message)
        if self.verbose:
            self.output_area.controls.append(ft.Text(value=message, selectable=True))
            self.output_area.scroll_to(offset=-1)

    def put_error(self, message: str):
        message = message.rstrip("\n")
        logging.error(message)
        self.output_area.controls.append(ft.Text(value=message, selectable=True, color=ft.Colors.RED_400))
        self.output_area.scroll_to(offset=-1)

    def put_status(self, message: str):
        message = message.rstrip("\n")
        self.tx_status.value = message
        self.tx_status.update()


class uiBuildView(ft.View):
    def __init__(self, *args):
        packages = []
        auto_exit = False
        if len(args) == 1 and isinstance(args[0], tuple):
            packages = args[0][0] if len(args[0]) else []
            auto_exit = args[0][1] if len(args[0]) > 1 else False
        else:
            packages = args[0] if len(args) else []
            auto_exit = args[1] if len(args) > 1 else False

        controls = [
            ft.AppBar(
                title=ft.Text(f"Building Packages"),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                automatically_imply_leading=False,
            ),
            uiBuild(packages, auto_exit),
        ]
        super().__init__("/build", controls=controls)
        self.vertical_alignment = ft.MainAxisAlignment.SPACE_BETWEEN
