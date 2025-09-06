```cmake
find_package(JPEG REQUIRED)
if(JPEG_FOUND)
  target_link_libraries(app PRIVATE JPEG::JPEG)
endif()
```

```cmake
find_package(libjpeg-turbo REQUIRED)
if(libjpeg-turbo_FOUND)
  target_link_libraries(app PRIVATE libjpeg-turbo::turbojpeg)
endif()
```
