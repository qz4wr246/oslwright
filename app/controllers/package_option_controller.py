from fletx import FletX
from fletx.core import FletXController, RxDict, RxList
from app.models.package_model import PackageModel
from app.models.package_option_ui_model import OptionUiItem
from app.services.package_service import PackageService
from app.services.platform_service import PlatformService
from app.core.evaluate import evaluate_str


class PackageOptionController(FletXController):
    def __init__(self):
        # print("PackageOptionController:__init__")
        super().__init__()

        self.package_service: PackageService = FletX.find(PackageService)  # type: ignore[arg-type]
        self.platform_service: PlatformService = FletX.find(PlatformService)  # type: ignore[arg-type]
        self.values: RxDict = self.create_rx_dict({})
        self.option_ui: RxList[OptionUiItem] = self.create_rx_list([])
        self.disabled: dict = {}

    def on_initialized(self):
        # print("PackageOptionController:on_initialized")
        self.modified = False

    def on_ready(self):
        # print("PackageOptionController:on_ready")
        pass

    def on_disposed(self):
        # print("PackageOptionController:on_disposed")
        pass

    def load_option(self, package: PackageModel):
        # print("PackageOptionController:load_option")
        self.package = package
        self.option = self.package_service.load_option(package)
        self.default_option = self.package_service.create_default_option(package)
        self.option_ui.value = self.package_service.load_option_ui(self.package).options
        session = self.platform_service.create_session_base(
            self.package, self.option.versions[self.option.current_version].options["msvc_version"]
        )
        for ui in self.option_ui.value:
            if isinstance(ui.items, str):
                ui.items = evaluate_str(ui.items, session)

        self.setup_value(self.option.current_version)
        self.update_disable()

    def setup_value(self, version):
        # print("PackageOptionController:setup_value")
        self.option.current_version = version
        for k, v in self.option.versions[version].options.items():
            self.values[k] = v

    def update_disable(self):
        # print("PackageOptionController:update_disable")
        session = self.platform_service.create_session_base(self.package)
        for k, v in self.values.value.items():
            session[k] = v

        for ui in self.option_ui.value:
            if isinstance(ui.enable, str):
                self.disabled[ui.name] = not bool(evaluate_str(ui.enable, session))
            else:
                self.disabled[ui.name] = not bool(ui.enable)

    def update_item(self, msvc_version):
        ui_items = self.package_service.load_option_ui(self.package).options
        session = self.platform_service.create_session_base(self.package, msvc_version)
        for ui in ui_items:
            if isinstance(ui.items, str):
                ui.items = evaluate_str(ui.items, session)
        self.option_ui.value = ui_items
        value = session["msvc_toolset_version_default"]
        self.values["msvc_toolset_version"] = value
        self.option.versions[self.option.current_version].options["msvc_toolset_version"] = value

    def update_value(self, name, value):
        # print("PackageOptionController:update_value")
        self.modified = True
        if name == "version":
            self.setup_value(value)
        if name == "msvc_version":
            self.update_item(value)

        self.values[name] = value
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
        self.package_service.revert_option(self.option)
        self.package_service.save_option(self.option)
