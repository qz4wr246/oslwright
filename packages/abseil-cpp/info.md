```cmake
find_package(absl REQUIRED)
target_link_libraries(myapp PRIVATE
    absl::base
    absl::strings
    absl::time
    absl::flat_hash_map
    absl::status
)
```

|モジュール名|主な機能・用途|
|---|---|
|absl::base|基本的なユーティリティ（メモリ管理、型変換など）|
|absl::strings|文字列操作（StrJoin, StrSplit, Substituteなど）|
|absl::time|日時・時間の処理|
|absl::synchronization|スレッド同期（Mutex, Notificationなど）|
|absl::random_random|ランダム生成（BitGen, Uniform, Exponentialなど）|
|absl::flat_hash_map|高速なハッシュマップ・セット|
|absl::status|エラーハンドリング（Status, StatusOr）|
|absl::flags|コマンドライン引数のパース|
|absl::log|ログ出力（|absl_LOG(INFO) など）|
|absl::numeric|数値演算ユーティリティ|
|absl::container|コンテナ関連（InlinedVector, btree_mapなど）|
