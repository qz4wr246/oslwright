from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Any, List


class Reason(Enum):
    NORMAL = auto()
    COMPLETED = auto()
    USER_INTERRUPTED = auto()
    ERROR = auto()
    EXCEPTION = auto()


@dataclass
class BuildModel:
    is_running: bool = False  # 処理中
    total_process_time: int = 0  # 処理時間
    processed_count: int = 0  # 処理数
    package_num: int = 0  # 対象数
    package_name: str = ""  # 処理中のパッケージ
    stage_name: str = ""  # ステージ
    status: str = ""
    reason: Reason = Reason.NORMAL
    message: str = ""
    build_force_packages: Optional[List[str]] = None  # 強制ビルドするパッケージ
