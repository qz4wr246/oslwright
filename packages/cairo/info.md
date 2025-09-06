```cmake
find_package(PkgConfig REQUIRED)
pkg_check_modules(cairo REQUIRED IMPORTED_TARGET cairo)
target_link_libraries(myapp PRIVATE PkgConfig::cairo)
```
