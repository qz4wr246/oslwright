```cmake
find_package(OpenGL REQUIRED)
include_directories(${OPENGL_INCLUDE_DIR})
find_package(glfw3 REQUIRED)
include_directories(${GLFW_INCLUDE_DIRS})

target_link_libraries(app PRIVATE glfw3)
```