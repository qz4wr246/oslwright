from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from dacite import Config, from_dict
import json
import hashlib

"""
PKG_NAME_options.jsonc
{
    "name: "sample",
    "versions": {
        "1.2.3": {
            "options": {
                "version": "6.0.4",
                "build_arch": "x64",
                "msvc_toolset_version": "vc144",
                "msvc_runtime_library": "md",
                "build_library": "shared",
                "build_type": "Release",
                "build_layout": "union",
                "cuda_enable": false,
                "cuda_version": null,
            },
            "stages": [
                {
                    "stage": "download",
                    "date": "2026/02/01 08:25:31"
                },
                {
                    "stage": "configure",
                    "date": "2026/02/01 08:28:47"
                },
                {
                    "stage": "build",
                    "date": "2026/02/01 08:41:48"
                },
                {
                    "stage": "install",
                    "date": "2026/02/01 08:41:50"
                },
                {
                    "stage": "post-install",
                    "date": "2026/02/01 08:41:51"
                }
            ]
        }
    }
}
"""


@dataclass
class PackageOptionStageItem:
    stage: str
    date: str


@dataclass
class PackageOptionItem:
    options: Dict[str, Any]
    stages: Optional[List[PackageOptionStageItem]] = None
    completed: Optional[str] = None


@dataclass
class PackageOptionModel:
    name: str
    current_version: str
    versions: Dict[str, PackageOptionItem]
    path: Optional[Path] = None

    # -------------------------
    # JSON / dict 変換メソッド
    # -------------------------

    def to_dict(self) -> Dict[str, Any]:
        """dataclass → dict（Path を文字列に変換）"""
        data = asdict(self)
        if data["path"] is not None:
            data["path"] = str(data["path"])
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PackageOptionModel":
        """dict → dataclass（dacite を使用）"""
        # Path を自動変換するための設定
        config = Config(type_hooks={Path: lambda x: Path(x) if x else None})
        return from_dict(data_class=cls, data=data, config=config)

    def clone(self) -> "PackageOptionModel":
        return PackageOptionModel.from_dict(self.to_dict())

    def has_diff(self, other: "PackageOptionModel") -> bool:
        return self.to_dict() != other.to_dict()

    def get_hash(self):
        d = self.versions[self.current_version].options.copy()
        d["name"] = self.name
        d_json = json.dumps(d, sort_keys=True)
        h_hex = hashlib.sha256(d_json.encode()).hexdigest()
        return int(h_hex, 16)
