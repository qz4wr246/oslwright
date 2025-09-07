#----------------------------------------------------------------------------
# Application rule
#----------------------------------------------------------------------------
set(target_name myapp)
add_executable(${target_name})

# app sources
set(app_sources
  main.cpp
  version.h
  $<$<CXX_COMPILER_ID:MSVC>:utf8.manifest>
  $<$<CXX_COMPILER_ID:MSVC>:resource.rc>
)
configure_file(resource.rc.in
              "${CMAKE_CURRENT_SOURCE_DIR}/resource.rc" @ONLY)

target_sources(${target_name} PRIVATE ${app_sources})

set_target_properties(${target_name}
  PROPERTIES
  DEBUG_POSTFIX "${CMAKE_DEBUG_POSTFIX}"
  MSVC_RUNTIME_LIBRARY "${MSVC_RUNTIME_LIBRARY}"
)
target_compile_features(${target_name} PRIVATE cxx_std_17)
target_compile_features(${target_name} PRIVATE c_std_17)
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
# genelate pdb file for Release build.
if(MSVC)
  # genalate pdb file for release
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
#----------------------------- End of file ----------------------------------
