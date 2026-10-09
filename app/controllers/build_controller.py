import threading
from datetime import datetime, timedelta
import time
import asyncio
import copy

import flet as ft

from ..models.build_model import BuildModel
from ..models.rich_text_model import RichText
from ..models.build_status_model import BuildStatusModel
from ..models.log_store import LogStore
from ..services.build_service import BuildService
from ..core.logger import PostLogger as Post
from ..core.common import seconds_to_hms
from ..services import get_service


class BuildController:
    """ """

    def __init__(self, page: ft.Page, on_status_change):
        # print("BuildController:__init__")
        self.page = page
        self.on_status_change = on_status_change
        self.build_service = get_service("BuildService")
        self.is_running = False
        self.process_time = 0
        self.remaining_time = 1
        self.packages = []
        self.model = BuildModel()
        self.build_force = False
        self.build_status = None

        # ログストアを初期化
        self.log_store = LogStore()
        self.max_lines = 500

        Post.setLogHooks(
            gui_hook=self.put_log,
            error_hook=self.put_error,
        )

    def set_build_packages(self, packages, build_force: bool = False):
        self.packages = packages
        self.build_force = build_force

    # ビルド開始
    def start_build(self):
        # print("BuildController:start_build")
        self.build_status = BuildStatusModel()
        self.build_status.build_force = self.build_force
        self.process_time = 0
        self.start_time = datetime.now()
        self.build_status.tx_start_time = self.start_time.strftime("%Y/%m/%d %H:%M:%S")
        if not self.is_running:
            self.is_running = True
            self.model = BuildModel()
            self.model.is_running = True
            if self.build_force:
                self.model.build_force_packages = [p.name for p in self.packages]
            self.build_service.run_build(self.packages, self.model)
            self.page.run_task(self._update_progress_task)

    async def _update_progress_task(self):
        while self.model.is_running:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass
            self.build_status.reason = self.model.reason
            self.process_time += 1
            self.remaining_time = self.model.total_process_time - self.process_time
            if self.remaining_time >= 0:
                self.build_status.tx_remaining_time_color = ft.Colors.PRIMARY
            else:
                self.build_status.tx_remaining_time_color = ft.Colors.RED
            self.build_status.tx_remaining_time = seconds_to_hms(self.remaining_time)
            if self.model.total_process_time:
                progress = self.process_time / self.model.total_process_time
            else:
                progress = 0.0
            self.build_status.progress = progress if progress <= 1.0 else 1.0
            completion_time = self.start_time + timedelta(seconds=self.model.total_process_time)
            self.build_status.tx_completion_time = completion_time.strftime("%Y/%m/%d %H:%M:%S")
            self.build_status.tx_elapsed_time = seconds_to_hms(self.process_time)
            self.build_status.tx_processed = f"{self.model.processed_count}/{self.model.package_num}"
            self.build_status.tx_status = f"{self.model.package_name} / {self.model.stage_name} {self.model.status}"
            # ビルドステータス更新
            status_data = copy.copy(self.build_status)
            self.on_status_change(status_data)

        # ビルドステータス更新
        status_data = copy.copy(self.build_status)
        self.on_status_change(status_data)
        self.is_running = False

    def stop_build(self):
        self.build_service.stop_build()

    def put_error(self, message: str):
        message = message.rstrip("\n")
        self.log_store.list.append(RichText(text=message, color=ft.Colors.ERROR))

        # 500行制限のロジック
        if len(self.log_store.list) > self.max_lines:
            self.log_store.list.pop(0)

    def put_log(self, message: str):
        message = message.rstrip("\n")
        self.log_store.list.append(RichText(text=message))

        # 500行制限のロジック
        if len(self.log_store.list) > self.max_lines:
            self.log_store.list.pop(0)
