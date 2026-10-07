# サービスレジストリ
_services = {}


def get_service(name: str):
    return _services.get(name)


# 遅延インポート（循環参照を防ぐため）
from .build_service import BuildService
from .package_service import PackageService
from .platform_service import PlatformService, PlatformReason, ReasonCode
from .app_setting_service import AppSettingService

__all__ = [
    "PlatformService",
    "PackageService",
    "BuildService",
    "AppSettingService",
    "PlatformReason",
    "ReasonCode",
]


def initialize_all_services_sync():
    """指定された順序で実行する"""

    # 1. 最下層の PlatformService を初期化
    _services["PlatformService"] = PlatformService()

    # 2. PlatformService に依存する PackageService を初期化
    _services["PackageService"] = PackageService()

    # 3. AppSettingService の初期化
    _services["AppSettingService"] = AppSettingService()

    # 4. PackageService に依存する BuildService を初期化
    _services["BuildService"] = BuildService()
