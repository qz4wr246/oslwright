```cmake
find_package(wxWidgets CONFIG REQUIRED COMPONENTS gl core base OPTIONAL_COMPONENTS net)
# find_package(wxWidgets CONFIG REQUIRED COMPONENTS mono)  # when wxBUILD_MONOLITHIC=ON
if(wxWidgets_USE_FILE)
    include(${wxWidgets_USE_FILE})
endif()
target_link_libraries(${target_name} PRIVATE wxWidgets::wxWidgets)
```