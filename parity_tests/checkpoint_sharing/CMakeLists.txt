cmake_minimum_required(VERSION 3.24)
project(checkpoint_sharing LANGUAGES CXX)
add_executable(checkpoint_probe checkpoint_probe.cpp)
target_compile_features(checkpoint_probe PRIVATE cxx_std_17)
