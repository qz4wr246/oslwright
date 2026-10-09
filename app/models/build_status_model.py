from dataclasses import dataclass, field
import flet as ft

from ..models.rich_text_model import RichText
from ..services.build_service import Reason


@dataclass
class BuildStatusModel:
    reason: Reason = Reason.NORMAL
    build_force: bool = False
    progress: float = 0.0
    tx_remaining_time_color: ft.Colors = ft.Colors.PRIMARY
    tx_remaining_time: str = "00:00:00"
    tx_start_time: str = "00:00:00"
    tx_completion_time: str = "0000/00/00 00:00:00"
    tx_elapsed_time: str = "00:00:00"
    tx_processed: str = "0/0"
    tx_status: str = ""
