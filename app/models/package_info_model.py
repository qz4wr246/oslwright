from dataclasses import dataclass
from typing import Optional


@dataclass
class PackageInfoModel:
    name: str
    display: str
    version: Optional[str]
    description: Optional[str]
    license: Optional[str]
    site: Optional[str]
    process_time: Optional[str]
    markdown: Optional[str]
