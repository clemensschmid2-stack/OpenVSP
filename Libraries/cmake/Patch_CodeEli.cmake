set(datetime_file "${CODEELI_SOURCE_DIR}/cmake/DetermineDateTime.cmake")
file(READ "${datetime_file}" datetime_contents)

string(FIND "${datetime_contents}" "if (WIN32)" windows_block_start)
string(FIND "${datetime_contents}" "elseif (UNIX)" unix_block_start)
if(windows_block_start EQUAL -1 OR unix_block_start EQUAL -1)
    message(FATAL_ERROR "Could not locate Code-Eli's Windows date/time block")
endif()

string(SUBSTRING "${datetime_contents}" 0 ${windows_block_start} before_windows_block)
string(SUBSTRING "${datetime_contents}" ${unix_block_start} -1 after_windows_block)
set(portable_windows_block [=[if (WIN32)
  string(TIMESTAMP ELI_DATE "%Y%m%d")
  string(TIMESTAMP ELI_TIME "%H%M%S")
  set(ELI_DATE_TIME_FOUND TRUE)
]=])

file(WRITE "${datetime_file}"
    "${before_windows_block}${portable_windows_block}${after_windows_block}")
