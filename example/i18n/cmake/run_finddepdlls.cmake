if(NOT DEFINED PS_FILE OR NOT DEFINED TEMP_DIR OR NOT DEFINED TARGET)
  message(FATAL_ERROR "PS_FILE, TEMP_DIR, and TARGET are required.")
endif()

string(RANDOM LENGTH 16 ALPHABET 0123456789abcdef __temp_id)
set(__path_file "${TEMP_DIR}/finddepdlls-${__temp_id}-paths.txt")
set(__exclude_file "${TEMP_DIR}/finddepdlls-${__temp_id}-excludes.txt")
set(__target_file "${TEMP_DIR}/finddepdlls-${__temp_id}-targets.txt")

string(REPLACE ";" "\n" __path_content "${SEARCH_PATHS}")
string(REPLACE ";" "\n" __exclude_content "${EXCLUDE_LIST}")
string(REPLACE ";" "\n" __target_content "${TARGET}")
file(WRITE "${__path_file}" "${__path_content}")
file(WRITE "${__exclude_file}" "${__exclude_content}")
file(WRITE "${__target_file}" "${__target_content}")

set(__command
  powershell -NoProfile -NonInteractive -executionpolicy Bypass
    -File "${PS_FILE}"
    -TargetFile "${__target_file}"
    -PathFile "${__path_file}"
    -ExcludeFile "${__exclude_file}"
)
if(DEFINED DESTINATION AND NOT DESTINATION STREQUAL "")
  list(APPEND __command -Dest "${DESTINATION}")
endif()

execute_process(
  COMMAND ${__command}
  OUTPUT_VARIABLE __output
  OUTPUT_STRIP_TRAILING_WHITESPACE
  ERROR_VARIABLE __error
  RESULT_VARIABLE __result
)
file(REMOVE "${__path_file}" "${__exclude_file}" "${__target_file}")

if(NOT "${__result}" STREQUAL "0")
  message(FATAL_ERROR "PowerShell finddepdlls.ps1 failed: ${__error}${__output}")
endif()

if(DEFINED RESULT_FILE AND NOT RESULT_FILE STREQUAL "")
  file(WRITE "${RESULT_FILE}" "${__output}")
endif()
