from pathlib import Path

import pyjson5

ROOT_DIR = Path(__file__).resolve().parent.parent
PACKAGE_DIR = ROOT_DIR / "packages"
OUTPUT_FILE = ROOT_DIR / "docs" / "package-list.md"


def markdown_cell(value: object) -> str:
    text = str(value if value is not None else "-")
    return text.replace("|", r"\|").replace("\r", " ").replace("\n", " ")


def package_row(package_file: Path) -> tuple[str, str, str, str, str]:
    package = pyjson5.decode(package_file.read_text(encoding="utf-8"))
    versions = package["versions"]
    version_names = [version for version in versions if version != "default"]
    latest = version_names[-1]
    stable = next(
        (version for version in reversed(version_names) if versions[version].get("stable") is True),
        None,
    )
    version = f"{stable} ({latest})" if stable else latest
    source = versions.get("default", {})
    source_urls = [
        f"{name.removesuffix('_url')}: {source[name]}" for name in ("git_url", "download_url") if source.get(name)
    ]
    return (
        package["display"],
        version,
        package.get("license", "-"),
        package.get("site", "-"),
        "<br>".join(source_urls) if source_urls else "-",
    )


def main() -> None:
    rows = [package_row(package_file) for package_file in PACKAGE_DIR.rglob("package.jsonc")]
    rows.sort(key=lambda row: row[0].casefold())

    lines = [
        "# パッケージ一覧",
        "",
        "`packages/**/package.jsonc` の定義から生成した一覧です。`stable: true` が指定されたバージョンがある場合は「安定バージョン（最新バージョン）」、ない場合は最新バージョンのみを表示します。Source には `versions.default.git_url` と `versions.default.download_url` を記載しています。",
        "",
        "| name | version | license | site | source |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend("| " + " | ".join(map(markdown_cell, row)) + " |" for row in rows)
    OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Generated {OUTPUT_FILE.relative_to(ROOT_DIR)} ({len(rows)} packages)")


if __name__ == "__main__":
    main()
