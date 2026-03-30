""" """

from fletx.navigation import router_config

from .core.constants import Routes
from .pages import PackageInfoPage, PackageSelectPage, PackageOptionPage, BuildPage, AppSettingPage


def setup_routes():
    router_config.add_routes(
        [
            {"path": Routes.HOME, "component": PackageSelectPage},
            {"path": Routes.PKG_INFO, "component": PackageInfoPage},
            {"path": Routes.PKG_OPTION, "component": PackageOptionPage},
            {"path": Routes.BUILD, "component": BuildPage},
            {"path": Routes.SETTING, "component": AppSettingPage},
        ]
    )
