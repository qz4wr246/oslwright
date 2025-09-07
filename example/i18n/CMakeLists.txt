cmake_minimum_required(VERSION 3.30)
#----------------------------------------------------------------------------
# Project rule
#----------------------------------------------------------------------------
# get version
file(STRINGS src/version.h version REGEX "#define[ \\t]+APP_VERSION[ \\t]+\".+\"")
string(REGEX MATCH "[0-9.]+" APP_VERSION "${version}" "")
project(opencv-app VERSION ${APP_VERSION} LANGUAGES C CXX)

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

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_C_STANDARD 17)
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
# subdirectory rule
#----------------------------------------------------------------------------
add_subdirectory(src)

# #----------------------------------------------------------------------------
# # Package rule
# #----------------------------------------------------------------------------
# # Package Infomations
# set(CPACK_PACKAGE_NAME "${PROJECT_NAME}")
# set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
# set(CPACK_PACKAGE_VENDOR "example.org")
# set(CPACK_PACKAGE_HOMEPAGE_URL "http://example.com/project")
# set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "${PROJECT_NAME} Installer")
# # set(CPACK_PACKAGE_DESCRIPTION "same application.")
# set(CPACK_PACKAGE_INSTALL_DIRECTORY "${PROJECT_NAME}")
# set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_SOURCE_DIR}/License.txt")

# # select cpack generator
# set(CPACK_GENERATOR "WIX")

# if ("${CPACK_GENERATOR}" STREQUAL "WIX")
#   cmake_path(SET CPACK_WIX_ROOT NORMALIZE "$ENV{USERPROFILE}\\.dotnet\\tools")
#   set(CPACK_WIX_VERSION 4)
#   # GUID
#   set(CPACK_WIX_UPGRADE_GUID "186000ca-bbc7-479d-93b6-69dd2e37fe3a")
#   set(CPACK_WIX_PRODUCT_GUID "03f8816f-bf0e-4120-9d1f-4918fd5f4cee")

#   # UI customize
#   set(CPACK_WIX_CULTURES "ja-JP")
#   # set(CPACK_WIX_PRODUCT_ICON "${CMAKE_SOURCE_DIR}/icon.ico")
#   # set(CPACK_WIX_UI_BANNER "${CMAKE_SOURCE_DIR}/banner.bmp")
#   # set(CPACK_WIX_UI_DIALOG "${CMAKE_SOURCE_DIR}/dialog.bmp")

#   # Select UI
#   set(CPACK_WIX_UI_REF "WixUI_FeatureTree")

#   # create menu folder
#   set(CPACK_WIX_PROGRAM_MENU_FOLDER "${PROJECT_NAME}")

# endif()
# include(CPack)

# # Installation types
# cpack_add_install_type(Full
#   DISPLAY_NAME "Install the application")

# # Components
# cpack_add_component(Application
#   DISPLAY_NAME "Application"
#   INSTALL_TYPES Full)

# cpack_add_component(Documentation
#   DISPLAY_NAME "Documentation"
#   INSTALL_TYPES Full)
#----------------------------- End of file ----------------------------------


