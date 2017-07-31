project(loonmod)


file(MAKE_DIRECTORY ${CMAKE_LOONLOCAL_CACHE}/loonmod)

configure_file(loonmod.zsh.in loonmod.zsh @ONLY)
install(PROGRAMS ${CMAKE_CURRENT_BINARY_DIR}/loonmod.zsh DESTINATION bin)

install(PROGRAMS mod_func.py moddb.py DESTINATION bin)

