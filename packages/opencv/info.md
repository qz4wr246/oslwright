# howto use opencv
cmakeでopencvを利用する
### 全部入り
```cmake
set(target_name app)
add_executable(${target_name})

find_package(OpenCV REQUIRED)
target_include_directories(${target_name} PRIVATE ${OpenCV_INCLUDE_DIRS})
target_link_libraries(${target_name} PRIVATE ${OpenCV_LIBS})

```

### 使用するモジュールを指定する
リンクするライブラリが絞られる。
```cmake
find_package(OpenCV REQUIRED COMPONENTS core highgui imgproc)
target_include_directories(app PRIVATE ${OpenCV_INCLUDE_DIRS})
target_link_libraries(app PRIVATE ${OpenCV_LIBS})
```
モジュールの一覧は次のサイトで確認できます。

https://docs.opencv.org/4.x/index.html


### GStreamer のプラグインDLLをビルドディレクトリへコピーする
```cmake
if(MSVC)
  # copy gstreamer plugins
  find_package(PkgConfig REQUIRED)
  pkg_check_modules(GSTREAMER REQUIRED gstreamer-1.0)
  if(GSTREAMER_FOUND)
    message(STATUS "Detecting GStreamer plugins")
    pkg_get_variable(GSTREAMER_PLUGINS_DIR gstreamer-1.0 pluginsdir)
    file(GLOB GSTREAMER_PLUGINS_DLLS "${GSTREAMER_PLUGINS_DIR}/*.dll")
    add_custom_command(TARGET ${target_name} POST_BUILD
                      COMMAND ${CMAKE_COMMAND} -E make_directory "$<TARGET_FILE_DIR:${target_name}>/gstreamer-1.0"
                      COMMAND ${CMAKE_COMMAND} -E copy_if_different
                      ${GSTREAMER_PLUGINS_DLLS}
                      "$<TARGET_FILE_DIR:${target_name}>/gstreamer-1.0"
                      COMMAND_EXPAND_LISTS)
    string(REPLACE "${GSTREAMER_PLUGINS_DIR}/" "" __PLUGINS_DLLS_REL "${GSTREAMER_PLUGINS_DLLS}")
    oslw_find_depdll(GSTREAMER_PLUGINS_DEPENDENT_DLLS
                     DLLS ${__PLUGINS_DLLS_REL}
                     WORKDIR ${GSTREAMER_PLUGINS_DIR})
    list(FILTER GSTREAMER_PLUGINS_DEPENDENT_DLLS EXCLUDE REGEX "lib/gstreamer-1.0")
    add_custom_command(TARGET ${target_name} POST_BUILD
                      COMMAND ${CMAKE_COMMAND} -E copy_if_different
                      ${GSTREAMER_PLUGINS_DEPENDENT_DLLS}
                      "$<TARGET_FILE_DIR:${target_name}>"
                      COMMAND_EXPAND_LISTS)
  endif()
endif()
if(MSVC)
  # copy external dlls to bindir.
  oslw_copy_depdll(TARGET ${target_name})
endif()

# Install
install(TARGETS ${target_name}
  RUNTIME DESTINATION bin COMPONENT Application
  LIBRARY DESTINATION lib COMPONENT Application
  ARCHIVE DESTINATION lib COMPONENT Application
)

if(MSVC)
  if(GSTREAMER_PLUGINS_DLLS)
    # install gstreamer plugins
    install(FILES ${GSTREAMER_PLUGINS_DLLS}
            DESTINATION bin/gstreamer-1.0 COMPONENT Application)
    install(FILES ${GSTREAMER_PLUGINS_DEPENDENT_DLLS}
            DESTINATION bin COMPONENT Application)
    # remove duplicated
    string(REGEX MATCHALL "[^/;]+.dll" EXCLUDE_DLLS "${GSTREAMER_PLUGINS_DEPENDENT_DLLS}")
  endif()
  # install external dlls to distdir
  oslw_install_depdll(
    TARGET ${target_name}
    DESTINATION bin
    COMPONENT Application
    EXCLUDE "${EXCLUDE_DLLS}"
  )
endif()
```


# opencv configuration settings
OSLWrightのSettingsとは別に、opencvのビルド構成を変更するには以下のファイルを編集します。

packages/opencv/cv_options.cmake
