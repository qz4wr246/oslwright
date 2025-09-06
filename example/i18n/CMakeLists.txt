cmake_minimum_required(VERSION 3.30)
#----------------------------------------------------------------------------
# Project rules
#----------------------------------------------------------------------------
# get version
file(STRINGS src/version.h version REGEX "#define[ \\t]+APP_VERSION[ \\t]+\".+\"")
string(REGEX MATCH "[0-9.]+" APP_VERSION "${version}" "")

project(i18n-app VERSION ${APP_VERSION} LANGUAGES C CXX)

if(MSVC)
  #---------------------------
  # Setup oslwright environment
  #---------------------------
  if (NOT CMAKE_TOOLCHAIN_FILE)
    # oslwrite module load
    include(${CMAKE_SOURCE_DIR}/cmake/oslwright.cmake)
  endif()
  if(OSLW_FRAMEWORK_PATH)
    set(CMAKE_PREFIX_PATH "${OSLW_FRAMEWORK_PATH}")
  endif()
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)


if(MSVC)
  set(CMAKE_CONFIGURATION_TYPES "Debug;Release" CACHE STRING "limited configs")
  # OSLWright's packages are built with the /MD (Multi-threaded DLL runtime) option. Applications must also be built with /MD, even for debug builds.
  set(MSVC_RUNTIME_LIBRARY "MultiThreadedDLL")
  set(CMAKE_DEBUG_POSTFIX "d")
  add_compile_options("/utf-8")
  add_compile_options("/Zc:__cplusplus")
else()
  add_compile_options("-fno-char8_t")
endif()

#----------------------------------------------------------------------------
# Application rules
#----------------------------------------------------------------------------
set(target_name myapp)
add_executable(${target_name})

# myapp sources
set(sources
  src/main.cpp
  $<$<CXX_COMPILER_ID:MSVC>:src/utf8.manifest>
  $<$<CXX_COMPILER_ID:MSVC>:src/resource.rc>
)

# generate resource.rc
configure_file(src/resource.rc.in "${CMAKE_CURRENT_SOURCE_DIR}/src/resource.rc" @ONLY)

target_sources(${target_name}
               PRIVATE ${sources})

set_target_properties(${target_name}
  PROPERTIES
  DEBUG_POSTFIX "${CMAKE_DEBUG_POSTFIX}"
  MSVC_RUNTIME_LIBRARY "${MSVC_RUNTIME_LIBRARY}"
)

target_compile_definitions(${target_name} PRIVATE NOMINMAX)

# optimize options
target_compile_options(${target_name} PRIVATE
#   $<$<CONFIG:Release>:/O2 /GL /Ob2 /Oi /Qpar /arch:AVX2>
  $<$<CONFIG:Release>:/O2 /GL /Ob2 /Oi /Qpar>
)

target_link_options(${target_name} PRIVATE
  $<$<CONFIG:Release>:/LTCG /OPT:REF /OPT:ICF /INCREMENTAL:NO>
)

#[[
if(MSVC)
  # genelate pdb file for release
  target_compile_options(${target_name} PRIVATE "$<$<CONFIG:Release>:/Zi>")
  target_link_options(${target_name} PRIVATE "$<$<CONFIG:Release>:/DEBUG>")
  target_link_options(${target_name} PRIVATE "$<$<CONFIG:Release>:/OPT:REF>")
  target_link_options(${target_name} PRIVATE "$<$<CONFIG:Release>:/OPT:ICF>")
endif()
#]]

if(MSVC)
  # set startup project for Visual Studio.
  set_property(DIRECTORY ${CMAKE_SOURCE_DIR} PROPERTY VS_STARTUP_PROJECT "${target_name}")
endif()

#---------------------------
# Dependecies
#---------------------------
find_package(cxxopts REQUIRED)
target_link_libraries(${target_name} PRIVATE cxxopts::cxxopts)

find_package(log4cplus CONFIG REQUIRED)
target_link_libraries(${target_name} PRIVATE log4cplus::log4cplus)

find_package(fmt CONFIG REQUIRED)
target_link_libraries(${target_name} PRIVATE fmt::fmt)

find_package(i18n-gettext CONFIG REQUIRED)
target_link_libraries(${target_name} PRIVATE i18n-gettext)

if(MSVC)
  # Copy external dlls to bindir.
  oslw_copy_depdll(
    TARGET ${target_name}
  )
endif()

#----------------------------------------------------------------------------
# Install rules
#----------------------------------------------------------------------------
install(TARGETS ${target_name}
  RUNTIME DESTINATION bin COMPONENT Application
  LIBRARY DESTINATION lib COMPONENT Application
  ARCHIVE DESTINATION lib COMPONENT Application
)
install(DIRECTORY "${CMAKE_SOURCE_DIR}/etc/"
        DESTINATION etc
        COMPONENT Application
        PATTERN "*.po" EXCLUDE
)

if(MSVC)
  # Install external dlls
  oslw_install_depdll(
    TARGET ${target_name}
    COMPONENT Application
  )
endif()
#[[
if(MSVC)
  # Install MSVC runtime libraries
  set(CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS_SKIP TRUE)
  include(InstallRequiredSystemLibraries)
  install(PROGRAMS ${CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS}
          DESTINATION bin
          COMPONENT Application)
endif()
#]]

#----------------------------------------------------------------------------
# Package rule
#----------------------------------------------------------------------------
#[[
# Package Infomations
set(CPACK_PACKAGE_NAME "${PROJECT_NAME}")
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_PACKAGE_VENDOR "example.org")
set(CPACK_PACKAGE_HOMEPAGE_URL "http://example.com/project")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "${PROJECT_NAME} Installer")
# set(CPACK_PACKAGE_DESCRIPTION "same application.")
set(CPACK_PACKAGE_INSTALL_DIRECTORY "${PROJECT_NAME}")
set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_SOURCE_DIR}/License.txt")

# select cpack generator
set(CPACK_GENERATOR "WIX")

if ("${CPACK_GENERATOR}" STREQUAL "WIX")
  cmake_path(SET CPACK_WIX_ROOT NORMALIZE "$ENV{USERPROFILE}\\.dotnet\\tools")
  set(CPACK_WIX_VERSION 4)
  # GUID
  set(CPACK_WIX_UPGRADE_GUID "186000ca-bbc7-479d-93b6-69dd2e37fe41")
  set(CPACK_WIX_PRODUCT_GUID "03f8816f-bf0e-4120-9d1f-4918fd5f4eed")

  # UI customize
  set(CPACK_WIX_CULTURES "ja-JP")
  # set(CPACK_WIX_PRODUCT_ICON "${CMAKE_SOURCE_DIR}/icon.ico")
  # set(CPACK_WIX_UI_BANNER "${CMAKE_SOURCE_DIR}/banner.bmp")
  # set(CPACK_WIX_UI_DIALOG "${CMAKE_SOURCE_DIR}/dialog.bmp")

  # Select UI
  set(CPACK_WIX_UI_REF "WixUI_FeatureTree")

  # create menu folder
  set(CPACK_WIX_PROGRAM_MENU_FOLDER "${PROJECT_NAME}")

endif()
include(CPack)

# Installation types
cpack_add_install_type(Full
  DISPLAY_NAME "Install the application")

# Components
cpack_add_component(Application
  DISPLAY_NAME "Application"
  INSTALL_TYPES Full)

cpack_add_component(Documentation
  DISPLAY_NAME "Documentation"
  INSTALL_TYPES Full)
#]]
#----------------------------- End of file ----------------------------------


