import os
import json5 as json
from core.common import get_data_path
from models.app_setting_model import AppSettingModel


class AppSettingService:
    def load(self) -> AppSettingModel:
        path = get_data_path("app-settings.jsonc")

        # デフォルト値
        defaults = {
            "arch": "x64",
            "toolset": "v143",
            "runtime": "md",
            "library": "shared",
            "cuda": False,
            "cuda_version": "10.0",
        }

        if not os.path.exists(path):
            return AppSettingModel(values=defaults)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 新しい項目が追加された場合に補完
        for k, v in defaults.items():
            if k not in data:
                data[k] = v

        return AppSettingModel(values=data)

    def save(self, model: AppSettingModel):
        path = get_data_path("oslwrite-settings.jsonc")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(model.values, f, indent=2)
