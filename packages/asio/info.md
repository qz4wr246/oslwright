
```cmake
find_package(asio REQUIRED)
target_link_libraries(myapp PRIVATE asio::asio)
target_compile_definitions(myapp PRIVATE
  ASIO_STANDALONE  # Boost 非依存で使うために必要
)
```