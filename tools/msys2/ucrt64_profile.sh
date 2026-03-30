#!/usr/bin/bash
if [ "$MSYSTEM" = "UCRT64" ]; then
  export PKG_CONFIG_PATH="/opt/ucrt64/lib/pkgconfig:$PKG_CONFIG_PATH"
  export PATH="/opt/ucrt64/bin:$PATH"
fi
