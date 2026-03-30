from dataclasses import dataclass
from typing import Optional, Any
from enum import Enum, auto
from .package_model import PackageModel
from .package_option_model import PackageOptionModel


@dataclass
class NodeModel:
    package: "PackageModel"
    option: "PackageOptionModel"
    parent: Optional["NodeModel"] = None
