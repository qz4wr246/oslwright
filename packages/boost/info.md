```cmake
# Boost の使用設定
set(Boost_USE_STATIC_LIBS ON)        # 静的リンク（必要に応じて OFF）
set(Boost_USE_MULTITHREADED ON)      # マルチスレッド対応
set(Boost_USE_STATIC_RUNTIME OFF)    # ランタイム設定（必要に応じて）

# Boost の必要なコンポーネントを指定
find_package(Boost REQUIRED COMPONENTS
    filesystem
    system
    thread
    program_options
)

add_executable(myapp main.cpp)

target_link_libraries(myapp PRIVATE
    Boost::filesystem
    Boost::system
    Boost::thread
    Boost::program_options
)
```
## Boost CMake COMPONENTS 一覧（v1.83.0）

|コンポーネント名|主な用途・機能概要|
|---|---|
|atomic|原子操作（スレッドセーフな値操作）|
|chrono|時間処理（std::chrono 拡張）|
|container|高度なコンテナ（flat_map など）|
|context|コンテキスト切り替え（コルーチン基盤）|
|contract|契約プログラミング|
|coroutine|コルーチン（非同期処理）|
|date_time|日付・時間ユーティリティ|
|exception|例外処理ユーティリティ|
|fiber|軽量スレッド（ファイバー）|
|filesystem|ファイル・ディレクトリ操作|
|graph|グラフアルゴリズム|
|graph_parallel|並列グラフ処理|
|headers|全 Boost ヘッダのインクルード|
|iostreams|ストリームフィルタ|
|json|JSON 処理|
|locale|ロケール・国際化|
|log|ログ出力|
|log_setup|ログ設定ユーティリティ|
|math_c99, math_c99f, math_c99l|C99 数学関数群（float, long 対応）|
|math_tr1, math_tr1f, math_tr1l|TR1 数学関数群|
|mpi, mpi_python|MPI 並列処理（Python バインディング含む）|
|nowide|Windows の文字コード変換|
|numpy|NumPy バインディング|
|prg_exec_monitor|テスト実行モニター|
|program_options|コマンドライン引数解析|
|python|Python バインディング|
|random|乱数生成|
|regex|正規表現|
|serialization|オブジェクトのシリアライズ|
|stacktrace_addr2line|スタックトレース（addr2line 使用）|
|stacktrace_basic|基本的なスタックトレース|
|stacktrace_noop|No-op スタックトレース|
|system|エラーコード・システム操作|
|test_exec_monitor|テスト実行モニター|
|thread|スレッド処理|
|timer|タイマー処理|
|type_erasure|型消去ユーティリティ|
|unit_test_framework|単体テストフレームワーク|
|url|URL 操作ユーティリティ|
|wave|C++ プリプロセッサライブラリ|
|wserialization|ワイド文字対応シリアライズ


* 参考 Boost CMake COMPONENTS 一覧
https://gist.github.com/beojan/2fbd1c926c4ce1cc5d99894d59f32530
