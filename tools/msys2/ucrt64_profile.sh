#!/usr/bin/bash
if [[ "$MSYSTEM" == "UCRT64" ]]; then
  export PKG_CONFIG_PATH="/opt/ucrt64/lib/pkgconfig:/opt/ucrt64/share/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"
  export CMAKE_PREFIX_PATH="/opt/ucrt64/lib${CMAKE_PREFIX_PATH:+:${CMAKE_PREFIX_PATH}}"
  export PATH="/ucrt64/bin:/opt/ucrt64/bin:$PATH"
  export LANG="ja_JP.UTF-8"
  export NO_COLOR=1
  export GCC_COLORS=""
fi
if [[ "$MSYSTEM" == "MSYS" ]]; then
  export PKG_CONFIG_PATH="/opt/ucrt64/lib/pkgconfig:/opt/ucrt64/share/pkgconfig:/ucrt64/lib/pkgconfig:/ucrt64/share/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}"
  export CMAKE_PREFIX_PATH="/opt/ucrt64/lib${CMAKE_PREFIX_PATH:+:${CMAKE_PREFIX_PATH}}"
  export PATH="/ucrt64/bin:/opt/ucrt64/bin:$PATH"
  export LANG="ja_JP.UTF-8"
  export NO_COLOR=1
  export GCC_COLORS=""
fi
