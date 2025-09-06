```cmake
find_package(SQLite3 REQUIRED)
if(SQLite3_FOUND)
  target_link_libraries(traget SQLite::SQLite3)
endif()
```
