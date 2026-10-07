import flet as ft


# Flet 1.0のリアクティブデコレータを付与
@ft.observable
class LogStore:
    def __init__(self):
        self.list = []  # ログを格納する配列
