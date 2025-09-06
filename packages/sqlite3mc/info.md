```cmake
find_package(sqlite3mc)
if(sqlite3mc_FOUND)
  target_link_libraries(app PRIVATE sqlite3mc)
endif()
```