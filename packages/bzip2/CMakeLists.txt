cmake_minimum_required(VERSION 3.30)

file(STRINGS bzlib_private.h version REGEX "#define[ \\t]+BZ_VERSION[ \\t]+\".+\"")
string(REGEX MATCH "[0-9.]+" BZ_VERSION "${version}" "")

project(bzip2 VERSION ${BZ_VERSION} LANGUAGES C)

include(GNUInstallDirs)

option(BZIP2_SKIP_TOOLS "" OFF)

if(CMAKE_BUILD_TYPE STREQUAL Debug)
    add_definitions(-DBZ_DEBUG)
endif()

if(MSVC)
#    set(MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
    add_compile_options("/utf-8")
endif()

set(CMAKE_DEBUG_POSTFIX d)

set(BZ2_SOURCES
    blocksort.c
    bzlib.c
    bzlib.h
    bzlib_private.h
    compress.c
    crctable.c
    decompress.c
    huffman.c
    randtable.c
)
add_library(libbzip2 ${BZ2_SOURCES})

target_include_directories(libbzip2 PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

set_target_properties(libbzip2 PROPERTIES
    DEBUG_POSTFIX d
    PUBLIC_HEADER bzlib.h
    EXPORT_NAME BZip2
    VERSION "${BZ2_VERSION}"
    SOVERSION 1.0)
add_library(BZip2::BZip2 ALIAS libbzip2)

if(BUILD_SHARED_LIBS)
    target_compile_definitions(libbzip2 PRIVATE -DBZ_BUILD_DLL)
endif()

if(MSVC)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
    add_definitions(-D_CRT_SECURE_NO_DEPRECATE)
    add_definitions(-D_CRT_NONSTDC_NO_DEPRECATE)
endif()

install(TARGETS libbzip2
    EXPORT bzip2-export
    PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

install(FILES bzlib.h DESTINATION include)

if(NOT BZIP2_SKIP_TOOLS)
    add_executable(bzip2 bzip2.c ${BZ2_SOURCES})
    target_link_libraries(bzip2 PRIVATE libbzip2)
    add_executable(bzip2recover bzip2recover.c ${BZ2_SOURCES})
    target_link_libraries(bzip2recover PRIVATE libbzip2)
    install(TARGETS bzip2 bzip2recover DESTINATION tools/bzip2)
endif()


include(CMakePackageConfigHelpers)
install(EXPORT bzip2-export
  FILE BZip2Targets.cmake
  NAMESPACE BZip2::
  DESTINATION lib/cmake/BZip2
  EXPORT_LINK_INTERFACE_LIBRARIES
)

write_basic_package_version_file(
  ${CMAKE_CURRENT_BINARY_DIR}/BZip2ConfigVersion.cmake
  COMPATIBILITY AnyNewerVersion
)

configure_package_config_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/Config.cmake.in"
    "${CMAKE_BINARY_DIR}/BZip2Config.cmake"
    INSTALL_DESTINATION lib/cmake/BZip2
)

install(FILES
  ${CMAKE_CURRENT_BINARY_DIR}/BZip2ConfigVersion.cmake
  ${CMAKE_CURRENT_BINARY_DIR}/BZip2Config.cmake
  DESTINATION lib/cmake/BZip2
)
