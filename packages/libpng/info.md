```cmake
find_package(PNG REQUIRED)
if(PNG_FOUND)
  target_link_libraries(app PRIVATE PNG::PNG)
endif()
```