import os
from pathlib import Path
from typing import List
import pyjson5 as json

from fletx import FletX
from fletx.core import FletXService

from ..core.evaluate import evaluate_str
from ..core.constants import STAGES_ORDER
from ..core.logger import PostLogger as Post
from ..models.package_info_model import PackageInfoModel
from ..models.package_model import PackageModel
from ..models.package_option_model import PackageOptionItem, PackageOptionModel
from ..models.package_option_ui_model import OptionUiItem, PackageOptionUiModel
from .platform_service import PlatformService


class PackageService(FletXService):
    """Package Service"""

    def __init__(self, *args, **kwargs):
        # print("PackageService:__init__")
        self.platform_service: PlatformService = FletX.find(PlatformService)  # type: ignore[arg-type]
        self.packages: List[PackageModel] = []
        # Init base class
        super().__init__(name="PackageService", auto_start=True, **kwargs)

    def on_start(self):
        """Do stuf here on PackageService start"""
        # print("PackageService:on_start")

    def on_stop(self):
        """Do stuf here on packageService stop"""
        # print("PackageService:on_stop")

    def load_packages(self, force: bool = False):
        if self.packages and not force:
            return
        self.packages.clear()
        package_files = self.platform_service.get_package_files()
        Post.info(f"Package loading {len(package_files)} packages.")
        for path in package_files:
            Post.info(f"[{path.parent.name}]")
            package = self.load_package_file(path)
            if package:
                self.packages.append(package)

    def get_packages(self) -> List[PackageModel]:
        return self.packages

    def find_package(self, name: str) -> PackageModel | None:
        return next((p for p in self.packages if name == p.name), None)

    def load_package_file(self, path: Path) -> PackageModel | None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                latest_version = list(data["versions"].keys())[-1]
                return PackageModel(
                    name=data["name"],
                    display=data["display"],
                    description=data["description"],
                    site=data["site"],
                    license=data["license"],
                    process_time=data["process_time"],
                    options=data["options"],
                    versions=data["versions"],
                    info=data.get("info"),
                    path=str(path),
                    latest_version=latest_version,
                )

        except json.Json5DecoderException as e:
            Post.gui(f"Syntax error in package file {path}:{e.message}")
            return None

        except Exception as e:
            Post.gui(f"Error loading package file {path}: {e}")
            return None

        return None

    def load_option_ui(self, package: PackageModel) -> PackageOptionUiModel:
        ui_list = []
        for opt in package.options:
            ui_list.append(
                OptionUiItem(
                    display=opt["display"],
                    name=opt["name"],
                    type=opt["type"],
                    default=opt["default"],
                    items=opt.get("items", []),
                    enable=opt.get("enable", True),
                )
            )
        ui = PackageOptionUiModel(ui_list)
        return ui

    def load_info(self, package: PackageModel) -> PackageInfoModel:
        markdown = "No additional information available."
        if package.info and package.path:
            path = package.path.parent / package.info
            if Path(package.info).is_absolute():
                path = Path(package.info)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    markdown = f.read()
        hours, remainder = divmod(package.process_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        process_time = "{}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
        return PackageInfoModel(
            name=package.name,
            display=package.display,
            version=package.latest_version,
            description=package.description,
            license=package.license,
            site=package.site,
            process_time=process_time,
            markdown=markdown,
        )

    def load_option(self, package: PackageModel) -> PackageOptionModel:
        """ """
        path = self.platform_service.option_rootdir / f"{package.name}_options.jsonc"
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return PackageOptionModel.from_dict(data)
        else:
            return self.create_default_option(package)

    def save_option(self, option: PackageOptionModel):
        if option.path:
            with option.path.open("w", encoding="utf-8", newline="\n") as f:
                json.dump(option.to_dict(), f, ensure_ascii=False, indent=2, quote_keys=True)

    def create_default_option(self, package: PackageModel, session: dict | None = None) -> PackageOptionModel:
        if not session:
            session = self.platform_service.create_session_base(package)

        option_ui = self.load_option_ui(package)
        orig_items = {}
        for opt in option_ui.options:
            orig_items[opt.name] = opt.default

        vers = self.get_versions(package)
        versions = {}
        for ver in vers:
            items = orig_items.copy()
            for k, v in items.items():
                if k == "version":
                    items[k] = ver
                    session[k] = ver
                else:
                    items[k] = evaluate_str(v, session) if isinstance(v, str) else v
                    session[k] = items[k]
            versions[ver] = PackageOptionItem(options=items, stages=None)
        path = self.platform_service.option_rootdir / f"{package.name}_options.jsonc"
        return PackageOptionModel(
            name=package.name, current_version=package.latest_version, versions=versions, path=path
        )

    def get_versions(self, package: PackageModel) -> List[str]:
        return [k for k in package.versions.keys() if k != "default"]

    def revert_option(
        self,
        option: PackageOptionModel,
        target_stage: str = "configure",
    ):
        option_stages = option.versions[option.current_version].stages
        if option_stages:
            # target_stage が定義にない場合はそのまま返す
            if target_stage not in STAGES_ORDER:
                return

            # 現在のリストに含まれているステージ名の集合を作成
            existing_stages = {item.stage for item in option_stages}

            # target_stage の位置を特定
            target_idx = STAGES_ORDER.index(target_stage)

            # 1つ前のステージを特定（一番最初の場合は自分自身）
            prev_idx = max(0, target_idx - 1)
            prev_stage = STAGES_ORDER[prev_idx]

            # 削除を開始するステージを決定
            if prev_stage in existing_stages:
                # 1つ前が実在するなら、target_stage 以降を削除
                remove_start_stage = target_stage
            else:
                # 1つ前が存在しないなら、その1つ前（prev_stage）以降を削除
                remove_start_stage = prev_stage

            # 削除対象となるステージ名のセットを作成
            remove_start_idx = STAGES_ORDER.index(remove_start_stage)
            to_remove = set(STAGES_ORDER[remove_start_idx:])

            # 削除対象に含まれない PackageOptionStageItem オブジェクトのみをリストで返す
            option_stages = [item for item in option_stages if item.stage not in to_remove]
            # stagesを巻き戻す
            option.versions[option.current_version].stages = option_stages
            option.versions[option.current_version].completed = None
