"""
Common utilities for the application.
"""

import os
import sys
import re
from pathlib import Path
import json
import hashlib


def get_app_root() -> Path:
    # exe 実行時
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    # Python 実行時
    return Path(__file__).resolve().parent.parent.parent


def get_data_path(*paths) -> Path:
    return get_app_root() / Path(*paths)


def get_assets_dir() -> Path:
    default_assets_dir = get_data_path("assets")
    return Path(os.environ.get("FLET_ASSETS_DIR", str(default_assets_dir))).resolve()


def Version(text):
    text = text.strip()
    parenthetical = re.search(r"\s+\(", text)
    if parenthetical:
        text = text[: parenthetical.start()]

    semver = re.fullmatch(
        r"(?:v|ver(?:sion)?|vol)?"
        r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
        r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
        r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?",
        text,
        re.IGNORECASE,
    )
    if semver:
        major, minor, patch, prerelease = semver.groups()
        core = tuple((0, int(part)) for part in (major, minor, patch))
        prerelease_parts = (
            tuple(
                (0, int(part)) if part.isdecimal() else (1, part.lower())
                for part in prerelease.split(".")
            )
            if prerelease
            else ()
        )
        return core, 0 if prerelease else 1, prerelease_parts

    # Fall back to natural numeric/text ordering for non-SemVer package tags.
    parts = re.findall(r"\d+|[a-zA-Z]+", text)
    if parts and parts[0].lower() in {"v", "ver", "version", "vol"}:
        parts = parts[1:]

    core_parts = []
    prerelease_parts = []
    in_prerelease = False
    for part in parts:
        if not in_prerelease and part.isdecimal():
            core_parts.append((0, int(part)))
        elif not in_prerelease:
            in_prerelease = True
            prerelease_parts.append((1, part.lower()))
        elif part.isdecimal():
            prerelease_parts.append((0, int(part)))
        else:
            prerelease_parts.append((1, part.lower()))

    return tuple(core_parts), 0 if in_prerelease else 1, tuple(prerelease_parts)


def add_path_env(path, new_paths_str):
    """ """
    # 1. OS標準のセパレータ（Windows: ';' / Linux: ':'）を取得
    sep = os.pathsep

    # 2. 現在のPATHを取得してリスト化
    current_paths = path.split(sep)

    # 3. 入力された複数のパス（セミコロン等で区切られた文字列）を分解
    # ※ 入力が ';' 固定の場合は .split(';')、OS依存なら .split(sep)
    raw_new_paths = new_paths_str.split(sep)

    # 4. 重複を除去しながら追加（順序を維持）
    for p in raw_new_paths:
        p = p.strip()  # 空白除去
        if not p:
            continue

        abs_p = os.path.abspath(p)
        if abs_p not in current_paths:
            current_paths.insert(0, abs_p)  # 先頭に追加（優先度高）

    # 5. 再結合して環境変数に反映
    return sep.join(current_paths)


def uniq_path_env(paths):
    # 1. OSに応じたセパレータ（Windows: ';' / Unix: ':'）で分割
    sep = os.pathsep
    current_path = paths

    # 2. 空の要素を除外しつつリスト化
    path_list = [p.strip() for p in current_path.split(sep) if p.strip()]

    # 3. 辞書のキーを利用して順序を保ったまま重複削除
    # Python 3.7+ では挿入順序が保証されます
    unique_paths = list(dict.fromkeys(path_list))

    # 4. 環境変数を更新
    return sep.join(unique_paths)


def dict_hash(d: dict):
    """ """
    d_json = json.dumps(d, sort_keys=True)
    h_hex = hashlib.sha256(d_json.encode()).hexdigest()
    return int(h_hex, 16)


def seconds_to_hms(seconds: int) -> str:
    minus = False
    if seconds < 0:
        minus = True
        seconds = -seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return "{}{:02}:{:02}:{:02}".format("-" if minus else "", int(hours), int(minutes), int(seconds))
