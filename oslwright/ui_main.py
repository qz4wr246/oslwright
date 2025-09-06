import glob
import logging
import os
import re
import subprocess
import sys
import time
from logging.handlers import RotatingFileHandler

import flet as ft
import nest_asyncio
from natsort import natsorted

from oslwright.ow_package import Package
from oslwright.ow_platform import Platform
from oslwright.ui_build import uiBuildView
from oslwright.ui_default_settings import uiDefaultSettingsView
from oslwright.ui_info import uiInfoView
from oslwright.ui_package import uiPackageView
from oslwright.ui_settings import uiSettingsView

nest_asyncio.apply()


def ui_main(page: ft.Page):
    pop_flag = False

    ui_package = uiPackageView(Platform())

    def on_route_change(e):
        nonlocal ui_package
        nonlocal pop_flag

        if pop_flag:
            pop_flag = False
        else:
            if page.route == "/":
                page.views.clear()
                page.views.append(ui_package)
            elif page.route == "/settings":
                page.views.append(uiSettingsView(page.views[-1].data))
            elif page.route == "/info":
                page.views.append(uiInfoView(page.views[-1].data))
            elif page.route == "/build":
                page.views.append(uiBuildView(page.views[-1].data))
            elif page.route == "/default_settings":
                page.views.append(uiDefaultSettingsView(page.views[-1].data))
        page.update()

    def on_view_pop(e):
        nonlocal pop_flag
        pop_flag = True
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.title = "OSLwright the open source library builder."
    page.theme_mode = ft.ThemeMode.DARK
    page.window.height = 700
    page.window.width = 900
    page.vertical_alignment = ft.MainAxisAlignment.SPACE_BETWEEN
    page.window.center()

    page.on_route_change = on_route_change
    page.on_view_pop = on_view_pop
    page.views.clear()
    page.go("/")


def oslwright_gui():
    if os.path.basename(sys.executable).lower() == "python.exe":
        rootdir = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
    else:
        rootdir = os.path.abspath(os.path.join(sys.executable, os.pardir))
    subprocess.run(["chcp.com", "65001"])
    os.environ["PYTHONUTF8"] = "1"
    logfile = os.path.join(rootdir, "Output.log")

    logs = glob.glob(os.path.join(rootdir, "Output.log.*"))
    if len(logs):
        logs = natsorted(logs, reverse=True)
        m = re.match(r".*\\Output.log.(\d+)", logs[0])
        for no in reversed(range(1, int(m.group(1)) + 1)):
            os.rename(os.path.join(rootdir, f"Output.log.{no}"), os.path.join(rootdir, f"Output.log.{no + 1}"))
    if os.path.isfile(logfile):
        os.rename(os.path.join(rootdir, "Output.log"), os.path.join(rootdir, "Output.log.1"))

    logging.basicConfig(
        handlers=[RotatingFileHandler(logfile, mode="w", maxBytes=1000000, backupCount=5)],
        level=logging.INFO,
        format="%(message)s",
        encoding="utf-8",
    )

    logging.info("\n#=============================================================================================")
    logging.info(time.strftime("# OSLwright Start. %Y-%m-%d %H:%M:%S"))
    logging.info("#=============================================================================================")

    ft.app(target=ui_main)


if __name__ == "__main__":
    oslwright_gui()
