
[VTK Getting Started](https://docs.vtk.org/en/latest/getting_started/index.html)

```cmake
find_package(VTK COMPONENTS
  CommonColor
  CommonCore
  FiltersSources
  InteractionStyle
  RenderingContextOpenGL2
  RenderingCore
  RenderingFreeType
  RenderingGL2PSOpenGL2
  RenderingOpenGL2
)

target_link_libraries(app PRIVATE ${VTK_LIBRARIES})
```