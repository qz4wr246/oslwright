# OSLWright パッケージ定義ファイル仕様


OSLWrightで使用されるパッケージ定義ファイル(package.jsonc)のフォーマット説明です。

---
## テンプレート

用途に応じてテンプレートを選択しパッケージディレクトリへコピーし、package.jsoncへ変更したうえで、ライブラリのビルド方法を記述する

  ### テンプレート一覧
  | **ファイル**| **用途**|
  | :--- | :---|
  | package-cmake.jsonc| CMakeでライブラリをビルドする|
  | package-meson.jsonc| mesonでライブラリをビルドする|
  | package-cmake-interface.jsonc| ヘッダオンリーライブラリをビルドする|

---
## フォーマット仕様

package.jsonc は、json5で記述します。

### 1. 基本情報 (Root)

パッケージのメタデータと基本設定を定義します。


| キー | 型 | 必須 | 説明 |
| :--- | :--- | :---: | :--- |
| `name` | string | ○ | パッケージの識別名 |
| `display` | string | ○ | 表示用の名前 |
| `description` | string | ○ | パッケージの説明文 |
| `site` | string (URI) | ○ | 公式サイト等のURL |
| `license` | string | ○ | ライセンス情報 |
| `process_time` | number | ○ | ビルド処理の目安時間 |
| `info` | string(Path) | - | 補足情報(markdownファイル名) |
| `options` | array | ○ | 利用可能なオプション設定のリスト |
| `versions` | object | ○ | バージョンごとの依存関係やビルド手順 |

---

### 2. オプション設定 (`options`)

ユーザーが選択可能な設定項目を定義します。<br>
オプション画面で設定可能な項目と変数を定義します。

| キー | 型 | 必須 | 説明 |
| :--- | :--- | :---: | :--- |
| `name` | string | ○ | 変数名 |
| `display` | string | ○ | 表示名 |
| `type` | string | ○ | `text`, `bool`, `choice` のいずれか |
| `default` | string / bool | ○ | デフォルト値 |
| `enable` | string / bool | - | オプション項目の有効化 （default: true）|
| `items` | array / string | △ | `type`が`choice`の場合のみ必須。選択肢のリスト |


#### 2.1 システム予約オプション

システム予約オプションはビルドに必須項目です。
パッケージ定義ファイルで使用する変数が定義されているので必ず記述のこと
|オプションname|説明|
| :--- | :--- |
|version|パッケージのバージョンを指定、|
|msvc_version|Visual Studioのバージョン|
|msvc_toolset_version|MSVC ツールセットバージョン|
|build_arch| アーキテクチャビット|
|msvc_runtime_library|MSVCランタイムライブラリ|
|build_library|staticライブラリかdynamicライブラリを生成|
|build_type|ReleaseかDebuビルド|
|build_layout|出力ディレクトリをReleaseとDebugで分けるか|
|cuda_enable|CUDAを使用、常に使用しない場合は、enableキーをfale, defaultキーをfalseに設定する|
|cuda_version|CUDAバージンの指定|


---

### 3. バージョン管理 (`versions`)
バージョンごとの詳細定義です。直下にバージョン名（例: `"1.0.0"`, `"latest"`）をキーとして記述します。<br>
バージョン名 "default" は共通定義です。各バージョンの定義は**オーバレイ機構**により共通設定をマージ・上書きします。

#### バージョン別オブジェクトの構造


| キー | 型 | 必須 | 説明 |
| :--- | :--- | :--- | :--- |
| `dependencies` | object | - | 依存パッケージ（パッケージ名: バージョン指定） |
| `environments` | object | - | 環境変数の設定（キー: 値） |
| `stages` | object | ○ | ビルド等の各ステージ定義（後述） |
| `(任意)` | any | - | 変数定義(キーが変数名、後述) |
---
#### 3.1 依存関係の定義 (`dependencies`)
パッケージ名に対し、**簡易指定（文字列）** または **詳細指定（オブジェクト）** で記述します。


| 形式 | 例 | 説明 |
| :--- | :--- | :--- |
| **簡易指定** | `"openssl": ">=3.2.0"` | バージョン条件を文字列で直接指定。 |
| **詳細指定** | `"sqlite3": { ... }` | 有効化条件や動的なパラメータを含めて指定。 |

##### 詳細指定オブジェクトのプロパティ

| キー | 型 | 必須 | 説明 |
| :--- | :--- | :---: | :--- |
| `version` | string | ○ | バージョン範囲指定（例: `1.0.1` or `=1.0.1` `>1.0` or `>=1.0;<=2.1` 演算子: `=`,`==`,`<`,`<=`,`>`,`>=`） |
| `enable` | bool / string | - | 有効/無効 |
| `(任意)` | string | - | 依存先へ渡すカスタムオプション（例: `cuda_enable` 等） |

---
### 4. ステージ定義 (`stages`)
ビルドやインストールの各工程を定義します。

**使用可能なステージ名:**
`download`, `patch`, `configure`, `build`, `test`, `install`, `post-install`

#### ステージ内の構造


| キー | 型 | 必須 | 説明 |
| :--- | :--- | :--- | :--- |
| `environments` | object | - | そのステージ限定の環境変数 |
| `scripts` | array | ○ |  実行するスクリプトのリスト（後述） |
| `(任意)` | any | - | 変数定義(キーが変数名、後述) |


#### スクリプト定義 (`scripts`)


| キー | 型 | 必須 | 説明 |
| :--- | :--- | :---: | :--- |
| `script` | string | ○ | 実行するコマンド |
| `message` | string | - | 実行時に表示するメッセージ |
| `chdir` | string | - | 実行時の作業ディレクトリ |
| `when` | string / bool | - | 実行条件 |
| `ignore_errors` | boolean | - | エラー発生時に無視して継続する |
| `fallback` | string | - | エラー時に実行
| `environments` | object | - | このスクリプト限定の環境変数 |

---

### 5. 変数定義
バージョン構造やステージ内の構造において、予約キー以外はキーを名前とした変数が定義されます。
#### 記述例
```
"versions": {
    "default": {
      "source_dir": "${source_rootdir}\\${name}-${version}", // <- source_dirが変数名
      ...
    }
}

```
### 6. 文字列値の変数展開と動的処理
文字列値の中では、変数の展開や Python コードによる動的な記述が可能です。

#### 展開のルール

| 記法 | 説明 | 例 |
| :--- | :--- | :--- |
| `$変数名` / `${変数名}` | 定義済みの変数やオプションの値を展開。 | `${name}-${version}` |
| `{{ python code }}` | Python コードとして評価し、結果を展開。 | `{{ '-static' if $build_library == 'static' else '' }}` |

#### 記述例
```json
// 変数展開とPythonコードの組み合わせ例
"dist_name": "${name}-${version}{{ '' if $build_library == 'interface' else '-' + $build_arch + (('-cu' + $cuda_version.replace('.','')) if $cuda_enable else '') }}",
"dist_dir_debug": "${dist_rootdir}\\${dist_name}{{ '-debug' if $build_layout == 'separation' else '' }}"
```

---

### 7. 組み込み変数一覧

#### 7.1 パス・ディレクトリ関連

| 変数名 | 説明 |
|--------|------|
| `$rootdir` | システムの実行ルートディレクトリ |
| `$package_rootdir` | パッケージ定義ファイルの格納ルート |
| `$source_rootdir` | ソースコードの展開・ビルド用ディレクトリ |
| `$dist_rootdir` | ビルド済みバイナリのインストール先ルート |
| `$cache_rootdir` | キャッシュ・ダウンロードファイルの保管先 |
| `$assets_rootdir`| アセットの格納ルート |
| `$package_dir` | 現在処理中のパッケージ定義が存在するパス |

#### 7.2 システム・開発環境関連

| 変数名 | 説明 |
|--------|------|
| `$msvc_generator` | CMake で使用する MSVC ジェネレータ名 |
| `$visual_studio_current` | 現在使用中の Visual Studio 情報 |
| `$msvc_version_default` | デフォルトのVisual Studio のバージョン|
| `$msvc_toolset_version_default` | デフォルトの MSVC ツールセット |
| `$build_arch_default` | デフォルトのビルドアーキテクチャ |
| `$cuda_root` | CUDA Toolkit のインストールルート |
| `$cuda_latest_version` | 検出された最新の CUDA バージョン |

#### 7.3 パッケージ・動的ステータス関連

| 変数名 | 説明 |
|--------|------|
| `$name` | パッケージの識別名 |
| `$version` | ビルド対象のバージョン番号|
| `$versions` | 利用可能な全バージョンのリスト |
| `$latest_version` | 最新バージョン番号 |
| `$pkg_config_path_release` | Release 用 pkg-config パス |
| `$pkg_config_path_release` | Debug 用 pkg-config パス |
| `$dependent_dlls_debug` | Release 用 依存 DLL のリスト |
| `$dependent_dlls_debug` | Debug 用 依存 DLL のリスト |
---

### 8. オーバレイ機構

バージョン定義は共通定義(default)をマージ・上書きします。


オーバレイ機構：マージコマンド一覧
キーの末尾に `!`コマンド を付加することで、マージ方法を制御できます。

| コマンド | 名称 | 辞書 (dict) の動作 | リスト (list) の動作 | 備考 |
|---|---|---|---|---|
| !a,!append | append | ネストされた辞書を再帰的にマージ | リストの末尾に要素を追加（拡張） | |
| !r,!replace | replace | 値を完全に置き換え | 値を完全に置き換え | 他のデータ型も置き換え |
| !d,!delete | delete | 該当するキーを削除 | - | |
| (なし) | default | 再帰的にマージ (!a と同等) | 完全に置き換え (!r と同等) | 標準の動作 |


#### 記述例
```json
{
  "versions":{
    "default":{
      // defaultの定義
    },
    "1.3.4": { // defaultの定義をベースに定義を上書きする
      "dependencies": { // sdlがdependencies へ追加または上書き
        "sdl!replace": {
          "version": ">=2.32.0"
        },
        "libxml2!delete":{} // libxml2 削除除
      },
      "stages": {
        "patch": { // バージョン1.3.4固有の patchステージを追加
          "patch_file_01": "${package_dir}/patch_file.diff",
          "scripts!append": [
            {
              "when": "{{not os.path.isfile(os.path.join($source_dir, '__patched_' + os.path.basename($patch_file_01)))}}",
              "chdir": "$source_dir",
              "script": "git apply \"$patch_file_01\" && copy nul > {{'__patched_' + os.path.basename($patch_file_01)}}"
            }
          ]
        }
      }
    },
    "1.4.5":{} // defaultの定義をそのまま継承する
  }
}
```
---

### 9.フォーマットの検証

パッケージファイル(pckage.jsonc)のフォーマットを検証する

```shell
python -m app.core.validator packages\__sample__\package.jsonc
```
