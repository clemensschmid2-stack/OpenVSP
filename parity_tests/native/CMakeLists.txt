cmake_minimum_required(VERSION 3.24)
project(vds_vspaero_validation LANGUAGES CXX)

# Build the exact pinned solver sources without OpenVSP's GUI/geometry library
# dependencies. Keep its source list and compile options authoritative.
get_filename_component(OPENVSP_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(VSP_NO_VSPAERO_OPT ON)
find_package(OpenMP REQUIRED COMPONENTS CXX)
if(MSVC)
  add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
endif()
foreach(config IN ITEMS Debug Release RelWithDebInfo MinSizeRel)
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/src/vsp/${config}")
endforeach()
file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/src/vsp")
enable_testing()
add_subdirectory("${OPENVSP_ROOT}/src/vsp_aero/Solver" solver)
add_subdirectory("${OPENVSP_ROOT}/parity_tests/profile_drag" profile_drag)
add_subdirectory("${OPENVSP_ROOT}/parity_tests/case_validity" case_validity)
add_subdirectory("${OPENVSP_ROOT}/parity_tests/checkpoint_sharing" checkpoint_sharing)
install(FILES "${OPENVSP_ROOT}/LICENSE" "${OPENVSP_ROOT}/MODIFICATIONS.md"
        DESTINATION .)

# Record paths using generator expressions, including multi-config Windows
# builds, instead of searching for possibly stale executables.
file(GENERATE OUTPUT "${CMAKE_BINARY_DIR}/executables-$<CONFIG>.txt"
     CONTENT "$<TARGET_FILE:vspaero>\n$<TARGET_FILE:checkpoint_probe>\n")
