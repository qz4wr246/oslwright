from fletx import FletX
from fletx.core import FletXController
from fletx.navigation import go_back

from ..models.package_info_model import PackageInfoModel
from ..services.package_service import PackageService


class PackageInfoController(FletXController):
    """ """

    def __init__(self):
        # print("PackageInfoController:__init__")
        super().__init__()
        self.package_service: PackageService = FletX.find(PackageService)  # type: ignore[arg-type]

    def on_initialized(self):
        """Called when controller is created and initialized"""
        # print("PackageInfoController:on_initialized")
        pass

    def on_ready(self):
        """Called when controller is ready (page is showing)"""
        # print("PackageInfoController:on_ready")
        pass

    def on_disposed(self):
        """Called when controller is destroyed"""
        # print("PackageInfoController:on_disposed")
        pass

    def get_package_info(self, package) -> PackageInfoModel:
        return self.package_service.load_info(package)

    def go_back(self):
        go_back()
