import argparse
import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import json5 as json
from jsonschema import Draft7Validator
from lark import Lark, Transformer, UnexpectedCharacters, UnexpectedToken, v_args

from .logger import PostLogger as Post
from .common import get_assets_dir

_pkg_schema_path = get_assets_dir() / "package.schema.json"
with open(_pkg_schema_path, "r", encoding="utf-8") as _f:
    pkg_json5_schema = json.load(_f)

_json_grammar = r"""
%import common.ESCAPED_STRING
%import common.CNAME
%import common.SIGNED_NUMBER
%import common.WS

%ignore WS

?start: value

?value: object
      | array
      | string
      | SIGNED_NUMBER      -> number
      | "true"             -> true
      | "false"            -> false
      | "null"             -> null

object : "{" pair? ("," pair)* ","? "}"
pair   : key ":" value

?key   : string
       | CNAME

array  : "[" value? ("," value)* ","? "]"

string : ESCAPED_STRING

COMMENT: /\/\/.*/ | /\/\*([\s\S]*?)\*\//
%ignore COMMENT
%ignore /[\t\f\r\n ]+/
"""

_system_valiable_names = {
    # built-in variable names
    "os": "os",
    "sys": "sys",
    "math": "math",
    "json": "json",
    "random": "random",
    "datetime": "datetime",
    "re": "re",
    "collections": "collections",
    "itertools": "itertools",
    # System variable names and their default values
    "rootdir": "C:/oslwright",
    "package_rootdir": "C:/oslwright/packages",
    "option_rootdir": "C:/oslwright/settings",
    "tools_rootdir": "C:/oslwright/tools",
    "cache_rootdir": "C:/oslwright/cache",
    "source_rootdir": "C:/oslwright/source",
    "dist_rootdir": "C:/oslwright/dist",
    "cuda_root": "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA",
    "cuda_versions": ["11.8", "11.7", "11.6"],
    "cuda_enable_default": True,
    "cuda_version_default": "11.8",
    "cuda_latest_version": "11.8",
    "msvc_toolset_version_default": "v142",
    "msvc_runtime_library_default": "md",
    "build_arch_default": "x64",
    "build_library_default": "static",
    "msvc_generator": "Visual Studio 16 2019",
    "cmake_generator_default": "Ninja",
    # session variables
    "package_dir": "C:/oslwright/packages/sample",
    "dependent_packages_debug": "",
    "dependent_packages_release": "",
    "pkg_config_path_debug": "",
    "pkg_config_path_release": "",
    "dependent_dlls_debug": "",
    "dependent_dlls_release": "",
}

_EXCLUDED_RESERVED_KEYS = [
    "options",
    "versions",
    "default",
    "dependencies",
    "environments",
    "stages",
    "scripts",
    "patch",
    "configure",
    "build",
    "test",
    "install",
    "post-install",
]


def format_error(category: str, message: str, line: int | None = None, column: int | None = None) -> str:
    """統一エラーメッセージを作成するヘルパー

    例: [ParseError] Line 3, Column 5: /message/
    """
    if line is not None and column is not None:
        return f"{category} at line {line}, column {column}: {message}"
    return f"{category} at line N/A, column N/A: {message}"


class Node:
    def __init__(self, value, meta):
        self.value = value
        self.meta = meta


class ASTBuilder(Transformer):
    @v_args(inline=True)
    def number(self, token):
        meta = getattr(token, "meta", None)
        if meta is None:
            line = getattr(token, "line", None) or getattr(token, "pos_in_stream", None) or 0
            column = getattr(token, "column", None) or 0
            meta = type("obj", (object,), {"line": line, "column": column})()
        return Node(float(token), meta)

    @v_args(inline=True)
    def string(self, token):
        # ESCAPED_STRING から引用符を削除して値を取得
        value = json.loads(str(token))
        meta = getattr(token, "meta", None)
        if meta is None:
            line = getattr(token, "line", None) or getattr(token, "pos_in_stream", None) or 0
            column = getattr(token, "column", None) or 0
            meta = type("obj", (object,), {"line": line, "column": column})()
        return Node(value, meta)

    def true(self, items):
        token = items[0] if items else None
        meta = token.meta if token else type("obj", (object,), {"line": 0, "column": 0})()
        return Node(True, meta)

    def false(self, items):
        token = items[0] if items else None
        meta = token.meta if token else type("obj", (object,), {"line": 0, "column": 0})()
        return Node(False, meta)

    def null(self, items):
        token = items[0] if items else None
        meta = token.meta if token else type("obj", (object,), {"line": 0, "column": 0})()
        return Node(None, meta)

    def pair(self, items):
        # items: [key_node, value_node]
        key_node, value_node = items
        return (key_node.value, value_node)

    def object(self, items):
        # items: list of pair tuples (key, value_node)
        obj_dict = {}
        first_meta = None
        for key, value_node in items:
            obj_dict[key] = value_node
            if first_meta is None:
                first_meta = value_node.meta

        meta = first_meta or type("obj", (object,), {"line": 0, "column": 0})()
        return Node(obj_dict, meta)

    def array(self, items):
        # items: list of value nodes; keep each element as a Node so we can track meta
        default_meta = type("obj", (object,), {"line": 0, "column": 0})()
        values = []
        for it in items:
            if isinstance(it, Node):
                values.append(it)
            else:
                # wrap primitive into Node with default meta
                values.append(Node(it, getattr(it, "meta", default_meta)))

        meta = items[0].meta if items and isinstance(items[0], Node) else default_meta
        return Node(values, meta)


def find_ast_node(ast_node, path):
    node = ast_node
    for key in path:
        if isinstance(node.value, dict):
            node = node.value[key]
        elif isinstance(node.value, list):
            node = node.value[int(key)]
        else:
            return None
    return node


def validate_package_json(pkgjson5_path: Path) -> None:
    """ """

    text = open(pkgjson5_path).read()
    parser = Lark(_json_grammar, start="start", parser="lalr")
    tree = None
    try:
        tree = parser.parse(text)
    except (UnexpectedToken, UnexpectedCharacters) as e:
        # Access attributes to create a custom message
        msg = f"Instead of '{e.token.value}', expected one of {', '.join(e.expected)}"
        Post.error(format_error("ParseError", msg, e.line, e.column))
        return

    ast = ASTBuilder().transform(tree)

    instance = None
    parse_error = None
    try:
        instance = json.loads(text)
    except Exception as e:
        parse_error = str(e)

    if parse_error:
        Post.error(format_error("ParseError", str(parse_error)))
    else:
        validator = Draft7Validator(pkg_json5_schema)
        errors = sorted(
            list(validator.iter_errors(instance)),
            key=lambda e: (
                find_ast_node(ast, list(e.path)).meta.line
                if find_ast_node(ast, list(e.path)) and hasattr(find_ast_node(ast, list(e.path)), "meta")
                else float("inf")
            ),
        )
        if not errors:
            pass  # No errors
        else:
            for err in errors:
                path = list(err.path)
                node = None
                try:
                    node = find_ast_node(ast, path)
                except Exception:
                    node = None

                if node and hasattr(node, "meta"):
                    line = node.meta.line
                    column = node.meta.column
                else:
                    line = "N/A"
                    column = "N/A"
                # If line/column are not numbers, omit them in formatted output
                if isinstance(line, int) and isinstance(column, int):
                    Post.error(format_error("SchemaValidationError", err.message, line, column))
                else:
                    Post.error(format_error("SchemaValidationError", err.message))

    def get_variable_names(node, path=None) -> List[dict]:
        var_names = []
        if path is None:
            path = []

        target_node = find_ast_node(node, path)
        if target_node is None:
            Post.error(format_error("Info", f"Path {path} not found"))
            return var_names

        if isinstance(target_node, Node):
            if isinstance(target_node.value, dict):
                for key, value in target_node.value.items():
                    if isinstance(value.value, list) or isinstance(value.value, dict):
                        var_names.extend(get_variable_names(node, path + [key]))
                    else:
                        var_names.append((key, value.value))

            elif isinstance(target_node.value, list):
                for idx, item in enumerate(target_node.value):
                    if isinstance(item.value, list) or isinstance(item.value, dict):
                        var_names.extend(get_variable_names(node, path + [idx]))

        return var_names

    package_variables: Dict[str, Any] = {}

    def validate_and_collect_variables(node, path=None, parent_key=None):
        if path is None:
            path = []

        target_node = find_ast_node(node, path)
        if target_node is None:
            return

        if isinstance(target_node, Node):
            if isinstance(target_node.value, dict):
                for key, value in target_node.value.items():
                    if isinstance(value, Node):
                        if isinstance(value.value, str):
                            # Validate code in string values
                            validate_code(
                                value.value,
                                package_variables,
                                base_lineno=value.meta.line,
                                base_colno=value.meta.column,
                            )
                            # Add to package_variables
                            package_variables[key] = value.value
                        elif isinstance(value.value, (dict, list)):
                            # Add dict/list values to package_variables unless reserved
                            if key not in _EXCLUDED_RESERVED_KEYS:
                                package_variables[key] = "any"
                            # Recursively process nested structures
                            validate_and_collect_variables(node, path + [key], parent_key=key)

            elif isinstance(target_node.value, list):
                for idx, item in enumerate(target_node.value):
                    if isinstance(item, Node) and isinstance(item.value, (dict, list)):
                        validate_and_collect_variables(node, path + [idx], parent_key=parent_key)

        # Extract package-level variables

    name = instance["name"] if "name" in instance else "unknown_package"  # type: ignore
    versions = [k for k in instance["versions"].keys() if k != "default"]  # type: ignore
    latest_version = versions[-1]

    # Initialize package_variables
    package_variables.update(
        {
            "name": name,
            "versions": versions,
            "latest_version": latest_version,
        }
    )
    # Initialize package_variables with system variables
    package_variables.update(_system_valiable_names)

    # Initialize package_variables with options' default values
    vars = get_variable_names(ast, path=["options"])

    vn = None
    for var in vars:
        if var[0] == "name":
            vn = var[1]
        if var[0] == "default":
            if vn:
                package_variables[vn] = var[1]
            vn = None

    # Validate code in versions
    validate_and_collect_variables(ast, path=["versions"])


# end of validate_package_json


_CODE_PATTERN = r"\{\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\}"
_VARIABLE_PATTERN = r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}|\$([a-zA-Z_][a-zA-Z0-9_]*)"
_ENVIRONMENT_PATTERN = r"%([a-zA-Z_][a-zA-Z0-9_]*)%"


def extract_code_blocks(val_str: str) -> List[Tuple[str, int, int]]:
    """{{...}}内のコードブロックを抽出"""
    blocks = []
    for match in re.finditer(_CODE_PATTERN, val_str):
        code = match.group(1)
        start = match.start()
        end = match.end()
        blocks.append((code, start, end))
    return blocks


def extract_acc_blocks(val_str: str) -> List[Tuple[str, int, int]]:
    """{{...}}以外のaccブロックを抽出"""
    blocks = []
    last_end = 0

    for match in re.finditer(_CODE_PATTERN, val_str):
        if match.start() > last_end:
            acc = val_str[last_end : match.start()]
            blocks.append((acc, last_end, match.start()))
        last_end = match.end()

    if last_end < len(val_str):
        acc = val_str[last_end:]
        blocks.append((acc, last_end, len(val_str)))

    return blocks


def extract_variables(text: str) -> List[Tuple[str, int, int]]:
    """テキストから変数を抽出（$foo または ${bar}の形式）"""
    variables = []
    for match in re.finditer(_VARIABLE_PATTERN, text):
        # グループ1: ${...}, グループ2: $...
        var_name = match.group(1) or match.group(2)
        start = match.start()
        end = match.end()
        variables.append((var_name, start, end))

    for match in re.finditer(_ENVIRONMENT_PATTERN, text):
        # グループ1: %...%
        var_name = match.group(1)
        start = match.start()
        end = match.end()
        variables.append((var_name, start, end))

    return variables


def replace_variables_in_code(code: str) -> Tuple[str, Dict[str, str]]:
    """コード内の変数を置換して、置換マッピングを返す"""
    replacements = {}
    modified_code = code.strip()

    # バージョンの高い順に処理（位置ズレを防ぐため後ろから）
    for var_name, start, end in sorted(extract_variables(modified_code), key=lambda x: x[1], reverse=True):
        original = modified_code[start:end]
        replacements[original] = var_name
        modified_code = modified_code[:start] + var_name + modified_code[end:]

    return modified_code, replacements


def find_undefined_variables(code: str) -> List[str]:
    """Pythonコードから未定義変数を検出（式として評価）"""
    code = code.strip()
    try:
        # 式として解析する
        tree = ast.parse(code, mode="eval")
    except SyntaxError as e:
        raise e

    # 定義済み変数を収集
    defined = set()
    undefined = set()

    class VariableVisitor(ast.NodeVisitor):
        def visit_Name(self, node):
            # 参照される変数
            if isinstance(node.ctx, ast.Load):
                if node.id not in defined:
                    undefined.add(node.id)
            self.generic_visit(node)

    visitor = VariableVisitor()
    visitor.visit(tree)

    return sorted(list(undefined))


def validate_code(val_str: str, var_names: dict, base_lineno=1, base_colno=1) -> bool:
    """
    val_strを検証:
    1. {{...}}内のコードを抽出
    2. {{...}}以外のaccを抽出
    3. コード内の変数($foo, ${bar})を置換して構文検証
    4. accから変数を抽出してvar_namesに存在するか検証
    """
    errors = []

    # 1. コードブロックを抽出
    code_blocks = extract_code_blocks(val_str)
    if not code_blocks:
        return  # コードがない場合は検証対象がない

    # 2. accブロックを抽出
    acc_blocks = extract_acc_blocks(val_str)

    # 3. accから変数を抽出して検証
    for acc, acc_start, acc_end in acc_blocks:
        acc_vars = extract_variables(acc)
        for var_name, var_start, var_end in acc_vars:
            if var_name not in var_names:
                # accの位置を考慮した絶対位置
                line_no = val_str[: acc_start + var_start].count("\n") + base_lineno
                col_no = acc_start + var_start - val_str.rfind("\n", 0, acc_start + var_start) + base_colno
                errors.append(format_error("CodeValidation", f"Undefined variable '${var_name}'", line_no, col_no))

    # 4. コードブロックを処理
    for code, code_start, code_end in code_blocks:
        # 変数を置換
        modified_code, replacements = replace_variables_in_code(code)

        # 構文検証
        syntax_errors = None
        try:
            ast.parse(modified_code)
        except SyntaxError as e:
            syntax_errors = e

        if syntax_errors:
            errors.append(
                format_error(
                    "SyntaxError",
                    syntax_errors.msg,
                    syntax_errors.lineno + base_lineno - 1,
                    syntax_errors.offset + base_colno - 1,
                )
            )
            continue

        # 未定義変数を検出
        try:
            undefined_vars = find_undefined_variables(modified_code)
        except SyntaxError as e:
            errors.append(format_error("SyntaxError", e.msg, e.lineno + base_lineno - 1, e.offset + base_colno - 1))
            continue

        for undef_var in undefined_vars:
            if undef_var not in var_names:
                line_no = val_str[:code_start].count("\n") + base_lineno
                col_no = code_start - val_str.rfind("\n", 0, code_start) + base_colno
                errors.append(format_error("CodeValidation", f"Undefined variable '{undef_var}'", line_no, col_no))
    # エラーを出力
    if errors:
        for error in errors:
            Post.error(error)
        return False
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate package.json5 files")
    parser.add_argument("file", help="Path to package.json5 file to validate")
    args = parser.parse_args()

    pkgjson5_path = Path(args.file)
    if not pkgjson5_path.exists():
        print(f"Error: File not found: {pkgjson5_path}")
        exit(1)

    print(f"Validating {pkgjson5_path}...")
    validate_package_json(pkgjson5_path)
    print("Validation completed.")
