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
        self.default_option = self.package_service.create_default_option(self.package)
        self.option = self.package_service.load_option(package)
        self.option_ui = self.package_service.load_option_ui(self.package).options
        for k, v in self.option.versions[self.option.current_version].options.items():
            self.values[k] = OptionItemValue(k, v, False)
        self.update_item()

    def update_item(self):
        session = self.platform_service.create_session_base(
            self.package, self.option.versions[self.option.current_version].options["msvc_version"]
        )
        for k, v in self.option.versions[self.option.current_version].options.items():
            session[k] = v
        self.option_ui = self.package_service.load_option_ui(self.package).options
        for ui in self.option_ui:
            if ui.type == "choice" and isinstance(ui.items, str):
                ui.items = evaluate_str(ui.items, session)
            if isinstance(ui.default, str):
                ui.default = evaluate_str(ui.default, session)

            if ui.type == "choice":
                v = self.option.versions[self.option.current_version].options[ui.name]
                if ui.items and not v in ui.items:
                    self.option.versions[self.option.current_version].options[ui.name] = ui.default
                    self.values[ui.name].value = ui.default

            if isinstance(ui.enable, str):
                self.values[ui.name].disabled = not bool(evaluate_str(ui.enable, session))
            else:
                self.values[ui.name].disabled = not bool(ui.enable)

    def update_value(self, name, value):
        # print("PackageOptionController:update_value")
        self.modified = True

        if name == "version":
            self.option.current_version = value

        self.option.versions[self.option.current_version].options[name] = value
        self.values[name].value = value
        self.update_item()

    def revert(self, stage: str) -> bool:
        ret = self.package_service.revert_option(self.option, stage)
        self.modified |= ret
        return self.modified

    def reset(self):
        self.modified = True
        self.option = self.default_option.clone()
        for k, v in self.option.versions[self.option.current_version].options.items():
            self.values[k] = OptionItemValue(k, v, False)
        self.update_item()

    def save(self):
        self.modified = False
        self.package_service.save_option(self.option)
