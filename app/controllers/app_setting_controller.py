from dataclasses import dataclass
from typing import Any

from app.models.app_setting_model import AppSettingModel
from app.models.package_option_ui_model import OptionUiItem

from app.services import get_service
from app.services.platform_service import PlatformService
from app.core.evaluate import evaluate_str


@dataclass
class SettingItemValue:
    name: str = ""
    value: Any = None
    disabled: bool = False


class AppSettingController:
    def __init__(self):
        # print("AppSettingController:__init__")

        self.platform_service: PlatformService = get_service("PlatformService")  # type: ignore[arg-type]
        self.values: dict[str, SettingItemValue] = {}
        self.setting_ui: list[OptionUiItem] = []
        self.app_setting: AppSettingModel | None = None
        self.modified = False

    def load_setting(self):
        self.app_setting = self.platform_service.load_setting()
        self.default_setting = self.platform_service.get_default_setting()
        setting_ui_dic = [
            {
                "display": "Visual Studio version",
                "name": "msvc_version_default",
                "enable": True,
                "type": "choice",
                "items": [msvc.generator for msvc in self.platform_service.visual_studio_infos],
                "default": self.default_setting.values["msvc_version_default"],
            },
            {
                "display": "Build arch",
                "name": "build_arch_default",
                "enable": True,
                "type": "choice",
                "items": ["x64", "x32"],
                "default": self.default_setting.values["build_arch_default"],
            },
            {
                "display": "MSVC toolset version",
                "name": "msvc_toolset_version_default",
                "enable": True,
                "type": "choice",
                "items": self.platform_service.msvc_toolset_versions,
                "default": self.default_setting.values["msvc_toolset_version_default"],
            },
            {
                "display": "MSVC runtime library",
                "name": "msvc_runtime_library_default",
                "enable": True,
                "type": "choice",
                "items": ["mt", "md"],
                "default": self.default_setting.values["msvc_runtime_library_default"],
            },
            {
                "display": "Build library",
                "name": "build_library_default",
                "enable": True,
                "type": "choice",
                "items": ["shared", "static", "shared;static"],
                "default": self.default_setting.values["build_library_default"],
            },
            {
                "display": "Using CUDA",
                "name": "cuda_enable_default",
                "enable": self.platform_service.cuda_enable_default,
                "type": "bool",
                "default": self.default_setting.values["cuda_enable_default"],
            },
            {
                "display": "CUDA Version",
                "name": "cuda_version_default",
                "enable": self.default_setting.values["cuda_enable_default"],
                "type": "choice",
                "items": self.platform_service.cuda_versions,
                "default": self.default_setting.values["cuda_version_default"],
            },
        ]
        self.setting_ui = []
        for opt in setting_ui_dic:
            self.setting_ui.append(
                OptionUiItem(
                    display=opt["display"],
                    name=opt["name"],
                    type=opt["type"],
                    default=opt["default"],
                    items=opt.get("items", []),
                    enable=opt.get("enable", True),
                )
            )

        for k, v in self.app_setting.values.items():
            self.values[k] = SettingItemValue(k, v, False)
        self.update_disable()

    def update_disable(self):
        # print("PackageOptionController:update_disable")
        session = self.platform_service.create_session_base()
        for k, v in self.values.items():
            session[k] = v.value

        for ui in self.setting_ui:
            if isinstance(ui.enable, str):
                self.values[ui.name].disabled = not bool(evaluate_str(ui.enable, session))
            else:
                self.values[ui.name].disabled = not bool(ui.enable)

    def update_value(self, key, value):
        if key == "cuda_version_default":
            next(item for item in self.setting_ui if item.name == "cuda_version_default").enable = value

        if key == "msvc_version_default":
            ui_items = self.setting_ui
            msvc_info = next(
                (info for info in self.platform_service.visual_studio_infos if info.generator == value), None
            )
            msvc_toolset_versions = [v.name for v in msvc_info.msvc_toolset_versions]
            msvc_toolset_version_default = msvc_info.msvc_toolset_versions[-1].name
            ui = next((ui for ui in ui_items if ui.name == "msvc_toolset_version_default"), None)
            ui.items = msvc_toolset_versions
            ui.default = msvc_toolset_version_default
            self.setting_ui = ui_items
            self.values["msvc_toolset_version_default"].value = msvc_toolset_version_default

        self.values[key].value = value
        self.app_setting.values[key] = value

    def save(self):
        converted_values = {item.name: item.value for item in self.values.values()}
        model = AppSettingModel(values=converted_values)
        self.platform_service.save_setting(model)

    def reset(self):
        self.app_setting = self.default_setting
        for key, value in self.app_setting.values.items():
            if key == "msvc_version_default":
                ui_items = self.setting_ui
                msvc_info = next(
                    (info for info in self.platform_service.visual_studio_infos if info.generator == value), None
                )
                msvc_toolset_versions = [v.name for v in msvc_info.msvc_toolset_versions]
                msvc_toolset_version_default = msvc_info.msvc_toolset_versions[-1].name
                ui = next((ui for ui in ui_items if ui["name"] == "msvc_toolset_version_default"), None)
                ui.items = msvc_toolset_versions
                ui.default = msvc_toolset_version_default
                self.setting_ui = ui_items
                self.values["msvc_toolset_version_default"].value = msvc_toolset_version_default
            if key == "msvc_toolset_version_default":
                continue
            self.values[key].value = value
