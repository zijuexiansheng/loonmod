cmake_minimum_required(VERSION 3.6)

project(loonmod-proj)

if(NOT DEFINED CMAKE_LOONLOCAL_CACHE)
    message(FATAL_ERROR CMAKE_LOONLOCAL_CACHE not defined)
endif()

file(MAKE_DIRECTORY ${CMAKE_LOONLOCAL_CACHE})

add_subdirectory(src)

message("-- [ROOT]: Install location is [${CMAKE_INSTALL_PREFIX}/bin]")
