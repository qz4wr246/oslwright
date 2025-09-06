```cmake
find_package(PkgConfig REQUIRED)
pkg_check_modules(HARFBUZZ REQUIRED IMPORTED_TARGET harfbuzz)
pkg_check_modules(HARFBUZZ_ICU REQUIRED IMPORTED_TARGET harfbuzz-icu)
pkg_check_modules(HARFBUZZ_CAIRO REQUIRED IMPORTED_TARGET harfbuzz-cairo)
pkg_check_modules(HARFBUZZ_SUBSET REQUIRED IMPORTED_TARGET harfbuzz-subset)
target_link_libraries(app PRIVATE
  PkgConfig::HARFBUZZ
  PkgConfig::HARFBUZZ_CAIRO
  PkgConfig::HARFBUZZ_ICU
  PkgConfig::HARFBUZZ_SUBSET
)
```