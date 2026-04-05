from typing import List
import logging
from fletx import FletX
from fletx.core import FletXController, RxList, Reactive
from fletx.navigation import navigate

from ..core.constants import Routes
from ..services.package_service import PackageService
from ..services.platform_service import PlatformService
from ..models.package_model import PackageModel
from ..models.platform_reason_model import PlatformReason, ReasonCode


class PackageSelectController(FletXController):
    """ """

    def __init__(self):
        # print("PackageSelectController:__init__")
        super().__init__()

    def on_initialized(self):
        """Called when controller is created and initialized"""
        # print("PackageSelectController:on_initialized")
        logging.disable(logging.NOTSET)  # flex logger hack
        self.platform_service: PlatformService = FletX.find(PlatformService)  # type: ignore[arg-type]
        self.package_service: PackageService = FletX.find(PackageService)  # type: ignore[arg-type]
        self.packages: RxList[PackageModel] = self.create_rx_list([])  # PackageModel のリスト
        self.platform_reason: Reactive[PlatformReason] = self.create_reactive(PlatformReason(ReasonCode.UNINITIALIZED))
        self.package_service.load_packages()
        logging.disable(logging.WARN)  # lex logger hack

    def on_ready(self):
        """Called when controller is ready (page is showing)"""
        # print("PackageSelectController:on_ready")
        self.platform_reason.value = self.platform_service.get_platform_reason()
        if self.platform_reason.value.code == ReasonCode.COMPLETE:
            self._set_packages()

    def on_disposed(self):
        """Called when controller is destroyed"""
        # print("PackageSelectController:on_disposed")
        pass

    def _set_packages(self):
        # print("PackageSelectController:_set_packages")
        self.packages.clear()
        packages = self.package_service.get_packages()
        self.packages.extend(packages)

    def open_option(self, package):
        navigate(Routes.PKG_OPTION, data={"package": package})

    def open_info(self, package):
        navigate(Routes.PKG_INFO, data={"package": package})

    def open_build(self, package):
        navigate(Routes.BUILD, data={"packages": [package]})

    def build_all(self, names: List[str]):
        name_set = set(names)
        selected_packages = [p for p in self.packages.value if p.name in name_set]
        if selected_packages:
            navigate(Routes.BUILD, data={"packages": selected_packages})

    def open_app_setting(self):
        navigate(Routes.SETTING)

    def reload(self):
        self.package_service.load_packages(force=True)
        self._set_packages()

    def install_tools(self):
        package_files = self.platform_service.get_tool_package_files()
        packages = []
        for file_path in package_files:
            packages.append(self.package_service.load_package_file(file_path))
        if len(packages):
            navigate(Routes.BUILD, data={"packages": packages, "build_force": True})
