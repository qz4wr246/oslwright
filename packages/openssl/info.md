```cmake
set(OPENSSL_USE_STATIC_LIBS TRUE) # If you need a static library.
find_package(OpenSSL CONFIG REQUIRED)
if(OpenSSL_FOUND)
  target_link_libraries(app PRIVATE OpenSSL::Crypto OpenSSL::SSL)
endif()
```