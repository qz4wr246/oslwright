#
# Copyright (c) 2025 qz4wr246 (https://github.com/qz4wr246)
# This software is released under the MIT License.
# See https://opensource.org/licenses/MIT
#

set(CMAKE_FIND_PACKAGE_PREFER_CONFIG ON)
#
#  Generate OSLW_FRAMEWORK_PATH
#
if(NOT OSLW_FRAMEWORK_PATH)
  if("${CMAKE_TOOLCHAIN_FILE}" MATCHES "oslwright.cmake$")
    cmake_path(GET CMAKE_TOOLCHAIN_FILE PARENT_PATH OSLW_CMAKE_DIR)
    file(REAL_PATH "${OSLW_CMAKE_DIR}" OSLW_CMAKE_DIR)
    set(_dist_root "${OSLW_CMAKE_DIR}/../dist")
  else()
    set(OSLW_CMAKE_DIR "${CMAKE_CURRENT_LIST_DIR}")
    if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/../3rdparty")
      set(_dist_root "${CMAKE_CURRENT_LIST_DIR}/../3rdparty")
    # elseif(EXISTS "${CMAKE_CURRENT_LIST_DIR}/../dist")
    #   set(_dist_root "${CMAKE_CURRENT_LIST_DIR}/../dist")
    endif()
  endif()
  if (_dist_root)
    set(_dist_list "")
    file(GLOB _dist_dirs LIST_DIRECTORIES true "${_dist_root}/*")
    foreach(item ${_dist_dirs})
      if(IS_DIRECTORY ${item})
        if(NOT "${item}" MATCHES "-debug$")
          file(REAL_PATH "${item}" _abs_dir)
          list(APPEND _dist_list "${_abs_dir}")
        endif()
      endif()
    endforeach()
    string(JOIN ";" OSLW_FRAMEWORK_PATH ${_dist_list})
  endif()
  find_program(_has_pkgconfig NAMES "pkg-config")
  if(NOT _has_pkgconfig)
    if(EXISTS "${OSLW_CMAKE_DIR}/../tools/pkg-config/bin/pkg-config.exe" AND NOT "${PKG_CONFIG_EXECUTABLE}")
      set(PKG_CONFIG_EXECUTABLE "${OSLW_CMAKE_DIR}/../tools/pkg-config/bin/pkg-config.exe")
    endif()
  endif()
endif()

#
#  find dumpbin.exe
#
find_program(DUMPBIN dumpbin)
if(DUMPBIN)
  cmake_path(GET DUMPBIN PARENT_PATH __MSVC_TOOLS_DIR)
else()
  cmake_path(GET CMAKE_CXX_COMPILER PARENT_PATH __MSVC_TOOLS_DIR)
endif()
file(TO_NATIVE_PATH ${__MSVC_TOOLS_DIR} __MSVC_TOOLS_DIR)
set(ENV{PATH} "${__MSVC_TOOLS_DIR};$ENV{PATH}")
unset(__MSVC_TOOLS_DIR)

#
# oslw_install_depdll(TARGET      <target>       target
#                    [DESTINATION <dir>]         Specify the directory which files will be installed.
#                    [COMPONENT   <component>]   Specify an installation component name.
#                    [PATH        <directories>] Semicolon-separated list of OSLW's package directories.
#                    [EXCLUDE     <dll-list>]    exclude dll list
#                    )
#
function(oslw_install_depdll)
  cmake_parse_arguments(_args "" "TARGET;DESTINATION;COMPONENT" "PATH;EXCLUDE" ${ARGN})
  set(_ps_file "${OSLW_CMAKE_DIR}/finddepdlls.ps1")
  set(_runner_file "${OSLW_CMAKE_DIR}/run_finddepdlls.cmake")
  if(NOT ${__args_TARGET})
    message(FATAL_ERROR "oslw_install_depdll(): Argument TARGET is required.")
  endif()

  if((NOT OSLW_FRAMEWORK_PATH) AND (NOT _args_PATH))
    message(FATAL_ERROR "oslw_install_depdll(): OSLW_FRAMEWORK_PATH and/or argument PATH are required.")
  endif()
  if(_args_PATH)
    set(__framework_path ${_args_PATH})
  else()
    set(__framework_path ${OSLW_FRAMEWORK_PATH})
  endif()
  if(_args_DESTINATION)
    if(NOT IS_ABSOLUTE "${_args_DESTINATION}")
      set(_args_DESTINATION "\"\${CMAKE_INSTALL_PREFIX}/${_args_DESTINATION}\"")
    else()
      set(_args_DESTINATION "\"${_args_DESTINATION}\"")
    endif()
  else()
    set(_args_DESTINATION "\"\${CMAKE_INSTALL_PREFIX}/bin\"")
  endif()

  list(JOIN __framework_path ";" __paths)
  string(JOIN ";" __excludes ${_args_EXCLUDE})
  string(RANDOM LENGTH 16 ALPHABET 0123456789abcdef __temp_id)
  set(__result_file "${CMAKE_CURRENT_BINARY_DIR}/finddepdlls-${__temp_id}.txt")
  set(__code "
        execute_process(
          COMMAND \${CMAKE_COMMAND}
            \"-DPS_FILE=${_ps_file}\"
            \"-DSEARCH_PATHS=${__paths}\"
            \"-DEXCLUDE_LIST=${__excludes}\"
            \"-DTARGET=\$<TARGET_FILE:${_args_TARGET}>\"
            \"-DRESULT_FILE=${__result_file}\"
            \"-DTEMP_DIR=${CMAKE_CURRENT_BINARY_DIR}\"
            -P \"${_runner_file}\"
          RESULT_VARIABLE __result
        )
        if(NOT \"\${__result}\" STREQUAL \"0\")
          message(FATAL_ERROR \"finddepdlls.ps1 failed with exit code \${__result}.\")
        endif()
        file(READ \"${__result_file}\" __deps)
        file(REMOVE \"${__result_file}\")
        file(INSTALL \${__deps} DESTINATION ${_args_DESTINATION})
    ")
  if(_args_COMPONENT)
    install(CODE "${__code}" COMPONENT "${_args_COMPONENT}")
  else()
    install(CODE "${__code}")
  endif()
  unset(__code)
  unset(__paths)
  unset(__framework_path)
endfunction()

#
# oslw_copy_depdll(TARGET   <target>       target
#                  [PATH    <directories>] Semicolon-separated list of OSLW's package directories.
#                  [EXCLUDE <dll-list>]    exclude dll list
#                 )
#
function(oslw_copy_depdll)
  cmake_parse_arguments(_args "" "TARGET" "PATH;EXCLUDE" ${ARGN})
  set(_ps_file "${OSLW_CMAKE_DIR}/finddepdlls.ps1")
  set(_runner_file "${OSLW_CMAKE_DIR}/run_finddepdlls.cmake")
  if(NOT ${__args_TARGET})
    message(FATAL_ERROR "oslw_copy_depdll(): Argument TARGET is required.")
  endif()
  if((NOT OSLW_FRAMEWORK_PATH) AND (NOT _args_PATH))
    message(FATAL_ERROR "oslw_copy_depd(): OSLW_FRAMEWORK_PATH and/or argument PATH are required.")
  endif()
  if(_args_PATH)
    set(__framework_path ${_args_PATH})
  else()
    set(__framework_path ${OSLW_FRAMEWORK_PATH})
  endif()
  list(JOIN __framework_path ";" __paths)
  string(JOIN ";" __excludes ${_args_EXCLUDE})
  add_custom_command(
    TARGET ${_args_TARGET}
    POST_BUILD
    COMMAND ${CMAKE_COMMAND}
      "-DPS_FILE=${_ps_file}"
      "-DSEARCH_PATHS=${__paths}"
      "-DEXCLUDE_LIST=${__excludes}"
      "-DTARGET=$<TARGET_FILE:${_args_TARGET}>"
      "-DDESTINATION=$<TARGET_FILE_DIR:${_args_TARGET}>"
      "-DTEMP_DIR=${CMAKE_CURRENT_BINARY_DIR}"
      -P "${_runner_file}"
  )
  unset(__paths)
  unset(__framework_path)
endfunction()

#
# oslw_find_depdll(<variable>              variable is assigned the result.
#                  DLLS     <dll paths>    Semicolon-separated list of DLLs path.
#                  [PATH    <directories>] Semicolon-separated list of OSLW's package directories.
#                  [EXCLUDE <dll-list>]    exclude dll list
#                  [WORKDIR <directory>]   workinng directory
#                 )
#
function(oslw_find_depdll arg)
  cmake_parse_arguments(_args "" "" "DLLS;PATH;EXCLUDE;WORKDIR" ${ARGN})
  set(_ps_file "${OSLW_CMAKE_DIR}/finddepdlls.ps1")
  set(_runner_file "${OSLW_CMAKE_DIR}/run_finddepdlls.cmake")
  if((NOT OSLW_FRAMEWORK_PATH) AND (NOT _args_PATH))
    message(FATAL_ERROR "oslw_find_depdll(): OSLW_FRAMEWORK_PATH and/or argument PATH are required.")
  endif()
  if(NOT _args_DLLS)
    message(FATAL_ERROR "oslw_find_depdll(): argument DLLS are required.")
  endif()
  if(_args_PATH)
    set(__framework_path ${_args_PATH})
  else()
    set(__framework_path ${OSLW_FRAMEWORK_PATH})
  endif()
  list(JOIN __framework_path ";" __paths)
  list(JOIN _args_DLLS ";" __dlls)
  string(JOIN ";" __excludes ${_args_EXCLUDE})
  string(RANDOM LENGTH 16 ALPHABET 0123456789abcdef __temp_id)
  set(__result_file "${CMAKE_CURRENT_BINARY_DIR}/finddepdlls-${__temp_id}.txt")
  execute_process(
    COMMAND ${CMAKE_COMMAND}
      "-DPS_FILE=${_ps_file}"
      "-DSEARCH_PATHS=${__paths}"
      "-DEXCLUDE_LIST=${__excludes}"
      "-DTARGET=${__dlls}"
      "-DRESULT_FILE=${__result_file}"
      "-DTEMP_DIR=${CMAKE_CURRENT_BINARY_DIR}"
      -P "${_runner_file}"
    # WORKING_DIRECTORY ${_args_WORKDIR}
    RESULT_VARIABLE __result
  )
  if(NOT "${__result}" STREQUAL "0")
    message(FATAL_ERROR "finddepdlls.ps1 failed with exit code ${__result}.")
  endif()
  file(READ "${__result_file}" __deps)
  file(REMOVE "${__result_file}")
  unset(__code)
  unset(__dlls)
  unset(__paths)
  unset(__framework_path)
  set(${arg} ${__deps} PARENT_SCOPE)
endfunction()
