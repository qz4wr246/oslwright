cmake_minimum_required(VERSION 3.30)

project(i18n-gettext VERSION 0.1.0 LANGUAGES CXX)

option(BUILD_SHARED_LIBS "" ON)

if(MSVC)
    # set(MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
    add_compile_options("/utf-8")
    set(CMAKE_DEBUG_POSTFIX d)
endif()

include_directories(I18NTest_vs2012/I18NTest/i18n)

set(public_header
    I18NTest_vs2012/I18NTest/i18n/Entry.h
    I18NTest_vs2012/I18NTest/i18n/I18nDefine.h
    I18NTest_vs2012/I18NTest/i18n/I18nUtils.h
    I18NTest_vs2012/I18NTest/i18n/MO.h
)

set(sources
    I18NTest_vs2012/I18NTest/i18n/Entry.cpp
    I18NTest_vs2012/I18NTest/i18n/I18nUtils.cpp
    I18NTest_vs2012/I18NTest/i18n/MO.cpp
)

add_library(i18n-gettext ${sources} ${public_header})

target_compile_definitions(i18n-gettext PRIVATE I18NGETTEXT_BUILD_INTERNAL)

if(NOT BUILD_SHARED_LIBS)
    target_compile_definitions(i18n-gettext PUBLIC I18NGETTEXT_STATIC_BUILD)
endif()

install(TARGETS i18n-gettext
    EXPORT i18n-gettext-export
    RUNTIME DESTINATION bin
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    INCLUDES DESTINATION include
    PUBLIC_HEADER DESTINATION include/i18n
)
install(
    FILES ${public_header}
    DESTINATION include/i18n
)

include(CMakePackageConfigHelpers)
install(EXPORT i18n-gettext-export
  FILE i18n-gettextConfig.cmake
  DESTINATION lib/cmake/i18n-gettext
  EXPORT_LINK_INTERFACE_LIBRARIES
)
write_basic_package_version_file(
  ${CMAKE_CURRENT_BINARY_DIR}/i18n-gettextConfigVersion.cmake
  COMPATIBILITY AnyNewerVersion
)
install(FILES
  ${CMAKE_CURRENT_BINARY_DIR}/i18n-gettextConfigVersion.cmake
  DESTINATION lib/cmake/i18n-gettext
)
