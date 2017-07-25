cmake_minimum_required(VERSION 3.6)

project(loonmod-proj)

file(MAKE_DIRECTORY ${CMAKE_INSTALL_PREFIX}/.loonlocalfiles/)

add_subdirectory(src)

message("-- [ROOT]: Install location is [${CMAKE_INSTALL_PREFIX}/bin]")
