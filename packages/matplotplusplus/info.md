```cmake
find_package(OpenGL)
find_package(glfw3 REQUIRED)
target_link_libraries(${target_name} PRIVATE glfw ${OPENGL_LIBRARY})
find_package(Matplot++ REQUIRED)
target_link_libraries(${target_name} PRIVATE Matplot++::matplot Matplot++::matplot_opengl)
```
