from ..models.package_info_model import PackageInfoModel
from ..services.package_service import PackageService
from ..services import get_service


class PackageInfoController:
    """ """

    def __init__(self):
        # print("PackageInfoController:__init__")
        self.package_service: PackageService = get_service("PackageService")  # type: ignore

    def get_package_info(self, package) -> PackageInfoModel:
        return self.package_service.load_info(package)
