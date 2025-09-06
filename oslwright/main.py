import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from oslwright.ui_main import oslwright_gui

if __name__ == "__main__":
    oslwright_gui()
