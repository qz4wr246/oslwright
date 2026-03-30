## uv をインストール

```cmd
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## .venvを作成
```
uv lock --prerelease allow
```

## OSLwright を実行する

```cmd
uv run main.py
```
