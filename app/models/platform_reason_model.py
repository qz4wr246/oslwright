from dataclasses import dataclass
from typing import Optional
from enum import Enum, auto


class ReasonCode(Enum):
    UNINITIALIZED = auto()
    COMPLETE = auto()
    MISSING_VISUALSTUDIO = auto()
    MISSING_BASE_TOOLS = auto()
    MISSING_EMBEDDED_TOOLS = auto()


@dataclass
class PlatformReason:
    code: ReasonCode = ReasonCode.UNINITIALIZED
    message: Optional[str] = ""
