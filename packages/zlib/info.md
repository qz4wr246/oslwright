```cmake
set(ZLIB_USE_STATIC_LIBS ON) # if you needs a static libaray.
find_package(ZLIB)
if(ZLIB_FOUND)
  target_link_libraries(app PRIVATE ZLIB::ZLIB)
endif()
```