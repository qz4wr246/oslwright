from dataclasses import dataclass, field
from typing import Any

from app.models.package_model import PackageModel
from app.models.package_option_ui_model import OptionUiItem
from app.services import get_service
from app.services.package_service import PackageService
from app.services.platform_service import PlatformService
from app.core.evaluate import evaluate_str


@dataclass
class OptionItemValue:
    name: str = ""
    value: Any = None
    disabled: bool = False


class PackageOptionController:
    def __init__(self):
        # print("PackageOptionController:__init__")
        self.package_service: PackageService = get_service("PackageService")  # type: ignore[arg-type]
        self.platform_service: PlatformService = get_service("PlatformService")  # type: ignore[arg-type]
        self.values: dict[str, OptionItemValue] = {}
        self.option_ui: list[OptionUiItem] = []
        self.modified = False

    def load_option(self, package: PackageModel):
        # print("PackageOptionController:load_option")
        self.package = package
        self.option = self.package_service.load_option(package)
        self.default_option = self.package_service.create_default_option(package)
        self.option_ui = self.package_service.load_option_ui(self.package).options
        session = self.platform_service.create_session_base(
            self.package, self.option.versions[self.option.current_version].options["msvc_version"]
        )
        for ui in self.option_ui:
            if isinstance(ui.items, str):
                ui.items = evaluate_str(ui.items, session)

        self.setup_value(self.option.current_version)
        self.update_disable()

    def setup_value(self, version):
        # print("PackageOptionController:setup_value")
        self.option.current_version = version
        for k, v in self.option.versions[version].options.items():
            self.values[k] = OptionItemValue(k, v, False)

    def update_disable(self):
        # print("PackageOptionController:update_disable")
        session = self.platform_service.create_session_base(self.package)
        for k, v in self.values.items():
            session[k] = v.value

        for ui in self.option_ui:
            if isinstance(ui.enable, str):
                self.values[ui.name].disabled = not bool(evaluate_str(ui.enable, session))
            else:
                self.values[ui.name].disabled = not bool(ui.enable)

    def update_item(self, msvc_version):
        ui_items = self.package_service.load_option_ui(self.package).options
        session = self.platform_service.create_session_base(self.package, msvc_version)
        for ui in ui_items:
            if isinstance(ui.items, str):
                ui.items = evaluate_str(ui.items, session)
        self.option_ui = ui_items
        value = session["msvc_toolset_version_default"]
        self.values["msvc_toolset_version"].value = value
        self.option.versions[self.option.current_version].options["msvc_toolset_version"] = value

    def update_value(self, name, value):
        # print("PackageOptionController:update_value")
        self.modified = True
        if name == "version":
            self.setup_value(value)
        if name == "msvc_version":
            self.update_item(value)

        self.values[name].value = value
        self.option.versions[self.option.current_version].options[name] = value

        self.update_disable()

    def revert(self):
        self.modified = True
        self.package_service.revert_option(self.option)
        self.update_disable()

    def reset(self):
        self.modified = False
        self.option = self.default_option.clone()
        self.update_item(self.option.versions[self.option.current_version].options["msvc_version"])
        self.setup_value(self.option.current_version)
        self.update_disable()

    def save(self):
        self.modified = False
        self.package_service.save_option(self.option)
