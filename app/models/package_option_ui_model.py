from dataclasses import asdict, dataclass, field
from typing import Any, List, Dict, Optional


@dataclass
class OptionUiItem:
    display: str
    name: str
    type: str  # "text" | "bool" | "choice"
    default: Any
    items: Optional[List[Any]] = field(default_factory=list)
    enable: Optional[Any] = True  # string | boolean


@dataclass
class PackageOptionUiModel:
    options: List[OptionUiItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
