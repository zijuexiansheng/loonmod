project(loonmod)


file(MAKE_DIRECTORY ${CMAKE_LOONLOCAL_CACHE}/loonmod)

set(CONFIG_FILE_NAMES loonmod.zsh)
foreach(fname ${CONFIG_FILE_NAMES})
    configure_file(${fname}.in ${fname} @ONLY)
    install(PROGRAMS ${CMAKE_CURRENT_BINARY_DIR}/${fname} DESTINATION bin)
endforeach()

install(PROGRAMS mod_func.py moddb.py DESTINATION bin)

