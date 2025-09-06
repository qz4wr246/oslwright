```cmake
find_package(libxml2 REQUIRED)
if(libxml2_FOUND)
  target_link_libraries(app PRIVATE LibXml2::LibXml2)
endif()
```
