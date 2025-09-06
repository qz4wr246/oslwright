```cmake
...
if (WIN32)
  find_package(dlfcn-win32 REQUIRED)
  set(CMAKE_DL_LIBS dlfcn-win32::dl)
endif ()
...
target_link_libraries(<target> ${CMAKE_DL_LIBS})
...
```