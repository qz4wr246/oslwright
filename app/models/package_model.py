from dataclasses import dataclass
from dataclasses_json import dataclass_json
from pathlib import Path
from typing import Any, List, Optional, Mapping


def make_hashable(obj):
    if isinstance(obj, dict):
        return frozenset((k, make_hashable(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return tuple(make_hashable(v) for v in obj)
    if isinstance(obj, Path):
        return str(obj)  # Path は文字列化して hashable に
    return obj


@dataclass_json
@dataclass(frozen=True)
class PackageModel:
    name: str
    display: str
    description: str
    site: str
    license: str
    process_time: float
    options: List[Mapping[str, Any]]
    versions: Mapping[str, Any]
    info: Optional[str] = None
    latest_version: Optional[str] = None
    path: Optional[str] = None
