from typing import Callable
import logging
from logging import getLogger, Handler


class _PostLogger:
    """"""

    def __init__(self):
        self.gui_hook: Callable[[str], None] | None = None
        self.info_hook: Callable[[str], None] | None = None
        self.debug_hook: Callable[[str], None] | None = None
        self.error_hook: Callable[[str], None] | None = None
        self.warning_hook: Callable[[str], None] | None = None
        self.critical_hook: Callable[[str], None] | None = None

        logging.disable(logging.NOTSET)
        logging.basicConfig(level=logging.INFO, force=True)

        self.logger: logging.Logger = getLogger("Oslwright")
        self.logger.setLevel(logging.DEBUG)

    def gui(self, message: str) -> None:
        if self.gui_hook:
            self.gui_hook(message)
        self.logger.info(message)

    def info(self, message: str) -> None:
        if self.info_hook:
            self.info_hook(message)
        self.logger.info(message)

    def debug(self, message: str) -> None:
        if self.debug_hook:
            self.debug_hook(message)
        self.logger.debug(message)

    def warning(self, message: str) -> None:
        if self.warning_hook:
            self.warning_hook(message)
        self.logger.warning(message)

    def error(self, message: str) -> None:
        if self.error_hook:
            self.error_hook(message)
        self.logger.error(message)

    def critical(self, message: str) -> None:
        if self.critical_hook:
            self.critical_hook(message)
        self.logger.critical(message)

    def setLogHooks(
        self,
        gui_hook: Callable[[str], None] | None = None,
        debug_hook: Callable[[str], None] | None = None,
        info_hook: Callable[[str], None] | None = None,
        warning_hook: Callable[[str], None] | None = None,
        error_hook: Callable[[str], None] | None = None,
        critical_hook: Callable[[str], None] | None = None,
    ):
        self.gui_hook = gui_hook
        self.debug_hook = debug_hook
        self.info_hook = info_hook
        self.warning_hook = warning_hook
        self.error_hook = error_hook
        self.critical_hook = critical_hook
        logging.disable(logging.NOTSET)

    def getLogger(self):
        return self.logger

    def addHandler(self, handler: Handler):
        logging.disable(logging.NOTSET)
        self.logger.addHandler(handler)


PostLogger = _PostLogger()
