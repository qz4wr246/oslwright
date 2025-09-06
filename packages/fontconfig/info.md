```cmake
find_package(PkgConfig REQUIRED)
pkg_check_modules(fontconfig REQUIRED IMPORTED_TARGET fontconfig)
target_link_libraries(myapp PRIVATE PkgConfig::fontconfig)
```
