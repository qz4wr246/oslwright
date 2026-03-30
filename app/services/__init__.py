"""
oslwright Application Services module.
"""

from fletx import FletX

from .build_service import BuildService
from .package_service import PackageService
from .platform_service import PlatformService, PlatformReason, ReasonCode

__all__ = ["PlatformService", "PackageService", "BuildService", "PlatformReason", "ReasonCode"]


def register_services():
    FletX.put(PlatformService())
    FletX.put(PackageService())
    FletX.put(BuildService())
