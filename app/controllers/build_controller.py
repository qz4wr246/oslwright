import threading
from datetime import datetime, timedelta
import time

import flet as ft
from fletx import FletX
from fletx.core import FletXController, RxList, RxStr, Reactive

from ..models.build_model import BuildModel
from ..models.rich_text_model import RichText
from ..services.build_service import BuildService
from ..core.logger import PostLogger as Post
from ..core.common import seconds_to_hms


class BuildController(FletXController):
    """ """

    def __init__(self):
        # print("BuildController:__init__")
        self.is_running = False
        self.process_time = 0
        self.remaining_time = 1
        self.max_lines = 500
        self.packages = []
        self.model = BuildModel()
        self.build_force = False
        super().__init__()

    def on_initialized(self):
        # print("BuildController:on_initialized")
        self.build_service: BuildService = FletX.find(BuildService)  # type: ignore[arg-type]
        self.model: BuildModel = BuildModel()
        self.tx_start_time: RxStr = self.create_rx_str("")
        self.tx_completion_time: RxStr = self.create_rx_str("")
        self.tx_remaining_time: RxStr = self.create_rx_str("")
        self.tx_remaining_time_color: Reactive[ft.Colors] = self.create_reactive(ft.Colors.PRIMARY)
        self.progress: Reactive[float] = self.create_reactive(0.0)
        self.tx_elapsed_time: RxStr = self.create_rx_str("")
        self.tx_processed: RxStr = self.create_rx_str("")
        self.tx_status: RxStr = self.create_rx_str("")

        self.logs: RxList[RichText] = RxList([])

    def on_ready(self):
        # print("BuildController:on_ready")
        Post.setLogHooks(
            gui_hook=self.put_log,
            error_hook=self.put_error,
        )

    def on_disposed(self):
        # print("BuildController:on_disposed")
        pass

    def set_build_packages(self, packages, build_force: bool = False):
        self.packages = packages
        self.build_force = build_force

    # --- ビルド開始 ---
    def start_build(self):
        # print("BuildController:start_build")
        self.process_time = 0
        self.start_time = datetime.now()
        self.tx_start_time.value = self.start_time.strftime("%Y/%m/%d %H:%M:%S")
        if not self.is_running:
            self.is_running = True
            self.model = BuildModel()
            self.model.is_running = True
            if self.build_force:
                self.model.build_force_packages = [p.name for p in self.packages]
            self.build_service.run_build(self.packages, self.model)
            task = threading.Thread(target=self._update_progress_task, daemon=True)
            task.start()

    def _update_progress_task(self):
        while self.model.is_running:
            time.sleep(1)
            self.process_time += 1
            self.remaining_time = self.model.total_process_time - self.process_time
            if self.remaining_time >= 0:
                self.tx_remaining_time_color.value = ft.Colors.PRIMARY
            else:
                self.tx_remaining_time_color.value = ft.Colors.RED
            self.tx_remaining_time.value = seconds_to_hms(self.remaining_time)
            if self.model.total_process_time:
                progress = self.process_time / self.model.total_process_time
            else:
                progress = 0.0
            self.progress.value = progress if progress <= 1.0 else 1.0
            completion_time = self.start_time + timedelta(seconds=self.model.total_process_time)
            self.tx_completion_time.value = completion_time.strftime("%Y/%m/%d %H:%M:%S")
            self.tx_elapsed_time.value = seconds_to_hms(self.process_time)
            self.tx_processed.value = f"{self.model.processed_count}/{self.model.package_num}"
            self.tx_status.value = f"{self.model.package_name} / {self.model.stage_name} {self.model.status}"

        self.is_running = False
        self.emit_local("build_finished", self.model.reason)

    # --- ビルド停止 ---
    def stop_build(self):
        self.build_service.stop_build()

    def put_log(self, message: str):
        message = message.rstrip("\n")
        self.logs.append(RichText(text=message))
        if len(self.logs.value) > self.max_lines:
            self.logs.pop(0)

    def put_error(self, message: str):
        message = message.rstrip("\n")
        self.logs.append(RichText(text=message, color=ft.Colors.ERROR))
        if len(self.logs.value) > self.max_lines:
            self.logs.pop(0)
