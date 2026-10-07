from typing import List
import logging


from ..core.constants import Routes
from ..services import get_service
from ..services.package_service import PackageService
from ..services.platform_service import PlatformService
from ..models.package_model import PackageModel
from ..models.platform_reason_model import PlatformReason, ReasonCode


class PackageSelectController:
    """ """

    def __init__(self):
        # print("PackageSelectController:__init__")
        logging.disable(logging.NOTSET)  # flex logger hack
        self.platform_service: PlatformService = get_service("PlatformService")  # type: ignore[arg-type]
        self.package_service: PackageService = get_service("PackageService")  # type: ignore[arg-type]
        self.packages: list[PackageModel] = []
        self.platform_reason: PlatformReason = PlatformReason(ReasonCode.UNINITIALIZED)
        self.package_service.load_packages()
        logging.disable(logging.WARN)  # flex logger hack
        self._set_packages()

    def on_initialized(self):
        """Called when controller is created and initialized"""
        # print("PackageSelectController:on_initialized")

    def _set_packages(self):
        # print("PackageSelectController:_set_packages")
        self.packages.clear()
        packages = self.package_service.get_packages()
        self.packages.extend(packages)

    def reload(self):
        self.package_service.load_packages(force=True)
        self._set_packages()
