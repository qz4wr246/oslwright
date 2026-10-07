import os
import re
import glob
import pathlib
import copy
from typing import Any

VAR_PATTERN = re.compile(r"\$(\w+)|\$\{\s*(\w+)\s*\}")
CODE_PATTERN = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)

# --- 追加: $$ を一時退避するためのプレースホルダ ---
ESCAPED_DOLLAR = "__ESCAPED_DOLLAR__"


class EvalSyntaxError(Exception):
    def __init__(self, message, original_string, offset):
        super().__init__(message)
        self.original_string = original_string
        self.offset = offset  # s 全体での offset
        self.code_pos = f"{original_string}\n{' ' * offset +'^'} "


def escape_dollars(s: str) -> str:
    """$$var → __ESCAPED_DOLLAR__var に変換"""
    return s.replace("$$", ESCAPED_DOLLAR)


def unescape_dollars(s: str) -> str:
    """__ESCAPED_DOLLAR__var → $var に戻す"""
    return s.replace(ESCAPED_DOLLAR, "$")


def replace_vars_in_code(code: str) -> str:
    """{{ ... }} 内の $var を var に置換"""

    def repl(m):
        return m.group(1) or m.group(2)

    code = escape_dollars(code)
    code = VAR_PATTERN.sub(lambda m: repl(m), code)
    code = unescape_dollars(code)
    return code


def replace_vars_in_text(text: str, variables: dict) -> str:
    """通常文字列内の $var を variables[var] に置換"""

    def repl(m):
        var = m.group(1) or m.group(2)
        return str(variables.get(var, ""))

    text = escape_dollars(text)
    text = VAR_PATTERN.sub(lambda m: repl(m), text)
    text = unescape_dollars(text)
    return text


def safe_eval_with_map(code, variables, s, match_start, mapping):
    try:
        variables = copy.deepcopy(variables)
        variables.update({"os": os, "re": re, "glob": glob, "pathlib": pathlib})
        return eval(code, variables)
    except NameError as e:
        new_offset = e.args[0].find("'")  # 例: "name 'foo' is not defined" から 'foo' の位置を探す
        if new_offset == -1:
            raise EvalSyntaxError(e.args[0], s, match_start) from e

        # 置換後 offset → 元の {{ code }} 内 offset
        old_offset_in_code = mapping[new_offset - 1]

        # 元の s 全体での offset
        old_offset_in_s = match_start + old_offset_in_code

        raise EvalSyntaxError(e.args[0], s, old_offset_in_s) from e
    except SyntaxError as e:
        new_offset = e.offset  # 置換後コードでの offset

        # 置換後 offset → 元の {{ code }} 内 offset
        old_offset_in_code = mapping[new_offset - 1]

        # 元の s 全体での offset
        old_offset_in_s = match_start + old_offset_in_code

        raise EvalSyntaxError(e.msg, s, old_offset_in_s)


def replace_vars_in_code_with_map(code: str):
    mapping = []
    new_code = []
    i = 0

    while i < len(code):
        m = VAR_PATTERN.match(code, i)
        if m:
            var = m.group(1) or m.group(2)
            replacement = var

            for _ in replacement:
                mapping.append(i)

            new_code.append(replacement)
            i = m.end()
        else:
            new_code.append(code[i])
            mapping.append(i)
            i += 1

    return "".join(new_code), mapping


def expand_envs_vars(s: str, envs: dict) -> str:
    """
    文字列中の %変数名% を envs 辞書の対応する値で置換する。
    """
    pattern = re.compile(r"%(\w+)%")

    def replace(match):
        var_name = match.group(1)
        # return envs.get(var_name, match.group(0))
        return envs.get(var_name, "")  # 存在しない変数は空文字に置換

    return pattern.sub(replace, s)


def evaluate_str(s: str, variables: dict, envs: dict | None = None) -> Any:
    s = s.strip()

    # --- 1. 全体が {{ code }} のみの場合 ---
    m = CODE_PATTERN.fullmatch(s)
    if m:
        original_code = m.group(1)
        replaced, mapping = replace_vars_in_code_with_map(original_code)
        return safe_eval_with_map(replaced, variables, s, m.start(1), mapping)

    # --- 2. 通常文字列として処理 ---
    def code_replacer(match):
        original_code = match.group(1)
        match_start = match.start(1)  # ← s 全体での開始位置

        replaced, mapping = replace_vars_in_code_with_map(original_code)

        # SyntaxError が起きたらここで safe_eval_with_map がログを出す
        result = safe_eval_with_map(replaced, variables, s, match_start, mapping)
        return str(result)

    # 2-1. 複数の {{ code }} を順番に処理
    s = CODE_PATTERN.sub(code_replacer, s)

    # 2-2. 通常文字列の $var を置換
    s = replace_vars_in_text(s, variables)

    return s


if __name__ == "__main__":
    vars = {"a": 10, "b": "fooo"}

    s = "Value is $${a}{{ 1 + $a}}, and next is {{ $b + 'zz' }} end"
    r = None
    try:
        r = evaluate_str(s, vars)
    except EvalSyntaxError as e:
        print(f"{e}")
        print(f"code:\n{e.code_pos}")

    print(r)
