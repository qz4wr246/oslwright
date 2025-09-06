cmake_minimum_required(VERSION 3.30)

file(STRINGS bzlib_private.h version REGEX "#define[ \\t]+BZ_VERSION[ \\t]+\".+\"")
string(REGEX MATCH "[0-9.]+" BZ_VERSION "${version}" "")

project(bzip2 VERSION ${BZ_VERSION} LANGUAGES C)

option(BZIP2_SKIP_TOOLS "" OFF)
option(BZIP2_SKIP_HEADERS "" OFF)

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
add_library(bz2 ${BZ2_SOURCES})
set_target_properties(bz2 PROPERTIES
    DEBUG_POSTFIX d
    VERSION "${BZ2_VERSION}"
    SOVERSION 1.0)
if(BUILD_SHARED_LIBS)
    target_compile_definitions(bz2 PRIVATE -DBZ_BUILD_DLL)
endif()

if(MSVC)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
    add_definitions(-D_CRT_SECURE_NO_DEPRECATE)
    add_definitions(-D_CRT_NONSTDC_NO_DEPRECATE)
endif()

install(TARGETS bz2
    EXPORT bzip2-export
    RUNTIME DESTINATION bin
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib)

if(NOT BZIP2_SKIP_TOOLS)
    add_executable(bzip2 bzip2.c ${BZ2_SOURCES})
    add_executable(bzip2recover bzip2recover.c ${BZ2_SOURCES})
    install(TARGETS bzip2 bzip2recover DESTINATION tools/bzip2)
endif()

if(NOT BZIP2_SKIP_HEADERS)
    install(FILES bzlib.h DESTINATION include)
endif()

include(CMakePackageConfigHelpers)
install(EXPORT bzip2-export
  FILE BZip2Config.cmake
  DESTINATION lib/cmake/BZip2
  EXPORT_LINK_INTERFACE_LIBRARIES
)
write_basic_package_version_file(
  ${CMAKE_CURRENT_BINARY_DIR}/BZip2ConfigVersion.cmake
  COMPATIBILITY AnyNewerVersion
)
install(FILES
  ${CMAKE_CURRENT_BINARY_DIR}/BZip2ConfigVersion.cmake
  DESTINATION lib/cmake/BZip2
)
