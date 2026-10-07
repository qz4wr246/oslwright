cmake_minimum_required (VERSION 3.10)

file(STRINGS "${CMAKE_SOURCE_DIR}/meson.build" version_line REGEX "version:[ \\t]+.+")
string(REGEX MATCH "[0-9]+(\\.[0-9]+)*" POCKETFFT_VERSION "${version_line}")

project (pocketfft VERSION ${POCKETFFT_VERSION})

add_library(${PROJECT_NAME} INTERFACE)
set_target_properties(${PROJECT_NAME}  PROPERTIES PUBLIC_HEADER "${PUBLIC_HEADERS}")
add_library(${PROJECT_NAME}::${PROJECT_NAME} ALIAS ${PROJECT_NAME})

target_include_directories(${PROJECT_NAME} INTERFACE
  $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}>
  $<INSTALL_INTERFACE:include>)

# include
install(
    DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/
    DESTINATION include
    FILES_MATCHING PATTERN "*.h"
)

install(TARGETS ${PROJECT_NAME}
  EXPORT ${PROJECT_NAME}-export
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  PUBLIC_HEADER DESTINATION include
  RUNTIME DESTINATION bin
)

include(CMakePackageConfigHelpers)
install(EXPORT ${PROJECT_NAME}-export
  FILE ${PROJECT_NAME}Targets.cmake
  NAMESPACE ${PROJECT_NAME}::
  DESTINATION lib/cmake/${PROJECT_NAME}
  EXPORT_LINK_INTERFACE_LIBRARIES
)

write_basic_package_version_file(
  ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake
  COMPATIBILITY AnyNewerVersion
)

configure_package_config_file(
    "${PROJECT_SOURCE_DIR}/Config.cmake.in"
    "${CMAKE_BINARY_DIR}/${PROJECT_NAME}Config.cmake"
    INSTALL_DESTINATION lib/cmake/${PROJECT_NAME}
)

install(FILES
  ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake
  ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake
  DESTINATION lib/cmake/${PROJECT_NAME}
)
