from fletx import FletX
from fletx.core import FletXController, RxDict, RxList
from fletx.navigation import go_back
from app.models.app_setting_model import AppSettingModel
from app.services.platform_service import PlatformService


class AppSettingController(FletXController):
    def __init__(self):
        # print("AppSettingController:__init__")
        super().__init__()
        self.platform_service: PlatformService = FletX.find(PlatformService)  # type: ignore[arg-type]
        self.values: RxDict = self.create_rx_dict({})
        self.setting_ui: RxList[dict] = self.create_rx_list([])
        self.app_setting: AppSettingModel | None = None

    def on_init(self):
        # print("AppSettingController:on_initialized")
        pass

    def on_ready(self):
        # print("AppSettingController:on_ready")
        pass

    def on_disposed(self):
        # print("AppSettingController:on_disposed")
        pass

    def load_setting(self):
        self.app_setting = self.platform_service.load_setting()
        self.default_setting = self.platform_service.get_default_setting()
        self.setting_ui.value = [
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

        for k, v in self.app_setting.values.items():
            self.values.value[k] = v

    def update_value(self, key, value):
        if key == "cuda_version_default":
            next(item for item in self.setting_ui.value if item["name"] == "cuda_version_default")["enable"] = value

        if key == "msvc_version_default":
            ui_items = self.setting_ui.value
            msvc_info = next(
                (info for info in self.platform_service.visual_studio_infos if info.generator == value), None
            )
            msvc_toolset_versions = [v.name for v in msvc_info.msvc_toolset_versions]
            msvc_toolset_version_default = msvc_info.msvc_toolset_versions[-1].name
            ui = next((ui for ui in ui_items if ui["name"] == "msvc_toolset_version_default"), None)
            ui["items"] = msvc_toolset_versions
            ui["default"] = msvc_toolset_version_default
            self.setting_ui.value = ui_items
            self.values["msvc_toolset_version_default"] = msvc_toolset_version_default

        self.values[key] = value
        self.app_setting.values[key] = value

    def save(self):
        model = AppSettingModel(values=self.values.value)
        self.platform_service.save_setting(model)

    def reset(self):
        self.app_setting = self.default_setting
        for key, value in self.app_setting.values.items():
            if key == "msvc_version_default":
                ui_items = self.setting_ui.value
                msvc_info = next(
                    (info for info in self.platform_service.visual_studio_infos if info.generator == value), None
                )
                msvc_toolset_versions = [v.name for v in msvc_info.msvc_toolset_versions]
                msvc_toolset_version_default = msvc_info.msvc_toolset_versions[-1].name
                ui = next((ui for ui in ui_items if ui["name"] == "msvc_toolset_version_default"), None)
                ui["items"] = msvc_toolset_versions
                ui["default"] = msvc_toolset_version_default
                self.setting_ui.value = ui_items
                self.values["msvc_toolset_version_default"] = msvc_toolset_version_default
            if key == "msvc_toolset_version_default":
                continue
            self.values[key] = value
