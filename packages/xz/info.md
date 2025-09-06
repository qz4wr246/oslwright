
```cmake
find_package(LZMA)
if(LIBLZMA_FOUND)
  target_link_libraries(app PRIVATE LibLZMA::LibLZMA)
endif()
```
