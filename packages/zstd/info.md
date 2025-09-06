```cmake
find_package(zstd)
if(zstd_FOUND)
  target_link_libraries(app PRIVATE zstd::libzstd)
endif()
```
