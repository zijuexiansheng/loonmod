# loonmod

A bash/zsh lib for manipulating PATH dynamically. This lib is similar to `module`.

# dependencies

* python
* cmake@3.10

# Install

## Use brew

`brew install zijuexiansheng/filbat/loonmod`

## install command 

`cmake -DCMAKE_INSTALL_PREFIX=<install root> -DCMAKE_LOONLOCAL_CACHE=<cache directory>`

# Usage

Add `source <install path>/bin/loonmod.zsh` to the `~/.zshrc` file. In order to dynamically change environment variables in your `bash/zsh` script, you can also `source` it at the beginning of your script

The first time you install and start to use it, you should use the command `mod_db db create` to create the database. If you install this module via `brew`, then you don't have to do that.

This module have two components, `mod_db` and `loonmod`

## `mod_db`

This is used to manage the database of your modules.

There are 5 subcommands for it, `insert, delete, update, list, db`. Type `mod_db <sub command> -h` for help. The following are some common usage:

* `insert`: add a module to the database
    * `mod_db insert <module name> /absolute/path/to/the/bin/direcotry`
    * `mod_db insert <module name> <bin path> -i <include path> -l <lib path>`
    * `mod_db insert <module name> <bin path> -d <module name>`
* `delete`:
    * `mod_db delete <module name>`
* `update`:
    * `mod_db update <module name> -p <bin path> -i <include path> -l <lib path> -d <module name>`
    * `mod_db update <module name> -I -L -D`
* `list`: There is a better command in `loonmod`. So it's not recommend to use this subcommand
    * `mod_db list -a`: show the names of all modules 
    * `mod_db list -n <module name>`: show detailed information of the module `<module name>`
* `db`:
    * `mod_db db create`: Create the database
    * `mod_db db cls`: clear the database **(dangerous!!! Don't use it unless you know what you are doing)**

**Note**: For subcommand `insert` and `update`, the options `-p, -i, -l, -d` can be used multiple times if there are multiple directories or dependencies for them

## `loonmod`

This command is used to manipulate the environment variables dynamically. For example, you installed an executable binary or script called `hello` in directory `$HOME/software/hello/bin`. And you've added a module name `hello` with command `mod_db insert hello ${HOME}/software/hello/bin`. Then you can execute `loonmod load hello`. After that, you can type `hello` to execute your binary or script.

`loonmod` has 7 subcommands, `avail, clear, depend, info, list, load, unload`. The following are the common commands:

* `avail`:
    * `loonmod avail`: list all the available modules
    * `loonmod avail -n <partial module name>`: list all the available modules that are sim
* `clear`:
    * `loonmod clear`: clear all the loaded modules
* `depend`:
    * `loonmod depend <module name>`: show the dependencies of a module
* `info`:
    * `loonmod info <module name>`: show module information
* `list`:
    * `loonmod list`: list all the loaded modules
    * `loonmod list -n <module name>`: list all the loaded modules that have name similar to `<module name>`
* `load`:
    * `loonmod load <module name>`: load module `<module name>`
* `unload`:
    * `loonmod unload <module name>`: unload module `<module name>`

**Notice:** Don't try to type `loonmod <sub command> -h`, as we wrote a wrapper for those sub commands.

