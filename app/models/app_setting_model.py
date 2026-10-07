from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Any, Dict


@dataclass_json
@dataclass
class AppSettingModel:
    values: Dict[str, Any]
