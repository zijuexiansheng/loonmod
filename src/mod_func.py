#!/usr/bin/env python2

import sys
import os
import argparse
import sqlite3

dirname = os.path.join( os.environ['LOONCONFIG'], "loonmod" )

class Sqlite:
    def __init__(self):
        self.open()

    def open(self):
        self.conn = sqlite3.connect(os.path.join(dirname, 'moddb.db'))
        self.cur = self.conn.cursor()

    def close(self):
        self.cur.close()
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def execute(self, stmt, params = None):
        if params:
            self.cur.execute(stmt, params)
        else:
            self.cur.execute(stmt)

    def fetchall(self):
        return self.cur.fetchall()

    def fetchone(self):
        return self.cur.fetchone()

def error_exit(msg, exit_code = 1):
    sys.stderr.write("[ERROR]: {}\n".format( msg ))
    sys.exit( exit_code )

def get_items(seq, attr, delimiter=':'):
    ret = []
    sql = Sqlite()
    for name in seq:
        sql.execute("select %s from module where name = ?" % attr, (name, ))
        res = sql.fetchone()
        if res and res[0]:
            ret += filter(None, res[0].split(delimiter))
    sql.close()
    return ret

env_strings = ["PATH", "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH", "LIBRARY_PATH", "LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH"]

def get_environs():
    global env_strings
    ret = {}
    for each in env_strings:
        ret[ each ] = filter(None, os.environ[ each ].split(":"))
    return ret

def print_environs(envs):
    global env_strings
    for each in env_strings:
        print each + "="
        print ":".join( envs[each] )

def list_safe_remove(listname, value):
    try:
        listname.remove( value )
    except ValueError:
        pass

def remove_path(envs, path_str):
    if not isinstance(path_str, list):
        list_safe_remove(envs["PATH"], path_str)
    else:
        for each_path in path_str:
            list_safe_remove(envs["PATH"], each_path)

def remove_incs(envs, incs_str):
    if not isinstance(incs_str, list):
        list_safe_remove(envs["C_INCLUDE_PATH"], incs_str)
        list_safe_remove(envs["CPLUS_INCLUDE_PATH"], incs_str )
    else:
        for each in incs_str:
            list_safe_remove(envs["C_INCLUDE_PATH"], each)
            list_safe_remove(envs["CPLUS_INCLUDE_PATH"], each )

def remove_libs(envs, libs_str):
    if not isinstance(libs_str, list):
        list_safe_remove( envs["LIBRARY_PATH"], libs_str )
        list_safe_remove( envs["LD_LIBRARY_PATH"], libs_str )
        list_safe_remove( envs["DYLD_LIBRARY_PATH"], libs_str )
    else:
        for each in libs_str:
            list_safe_remove( envs["LIBRARY_PATH"], each )
            list_safe_remove( envs["LD_LIBRARY_PATH"], each )
            list_safe_remove( envs["DYLD_LIBRARY_PATH"], each )


def handle_avail(args):
    sql = Sqlite()
    if args.name:
        sql.execute("select name from module where name like ?", ('%' + args.name + '%', ))
    else:
        sql.execute("select name from module")
    names = [name[0] for name in sql.fetchall()]
    sql.close()
    names.sort()
    print "\n".join(names)
        
def handle_clear(args):
    seq = args.seq.strip()
    if seq:
        seq = filter(None, seq.split(","))
        paths = get_items(seq, "path")
        incs = get_items(seq, "inc")
        libs = get_items(seq, "lib")

        envs = get_environs()
        remove_path(envs, paths)
        remove_incs(envs, incs)
        remove_libs(envs, libs)

        print_environs( envs )
    print "END"

def handle_depend(args):
    dep = get_items([args.name], "dependency", ',')
    if dep:
        if args.unloaded_dependencies:
            if args.seq == None:
                error_exit("--seq is required")
            mod_seq = filter(None, args.seq.split(","))
            for each in dep:
                if each in mod_seq:
                    continue
                print each
        else:
            print "\n".join( dep )            
    else:
        print "\n"

def handle_info(args):
    sql = Sqlite()
    sql.execute("select * from module where name = ?", (args.name, ))
    result = sql.fetchone()
    sql.close()

    if result:
        print "Info for module [args]"
        print "module name: [{}]".format( result[1] )
        print "module bin path: [{}]".format( result[2] )
        if result[3]:
            print "module include path: [{}]".format( result[3] )
        if result[4]:
            print "module library path: [{}]".format( result[4] )
        if result[5]:
            if args.seq == None:
                print "module dependencies:"
                for each in filter(None, result[5].split(",")):
                    print "\t* [{}]".format( each )
            else:
                print "module dependencies (mark loaded):"
                loaded_modules = filter(None, args.seq.split(","))
                for each in filter(None, result[5].split(",")):
                    if each in loaded_modules:
                        print "\t* [{}]    (loaded)".format( each )
                    else:
                        print "\t* [{}]".format( each )
    else:
        error_exit("Module [{}] doesn't exist".format( args.name ))

def handle_list(args):
    loaded_modules = filter(None, args.seq.split(","))
    if args.name:
        for each in loaded_modules:
            if each.find( args.name ) != -1:
                print each
    else:
        print "\n".join( loaded_modules )

def handle_load(args):
    loaded_modules = filter(None, args.seq.split(","))
    if args.name in loaded_modules:
        print "LOADED"
        return
    sql = Sqlite()
    sql.execute("select * from module where name = ?", (args.name, ))
    result = sql.fetchone()
    sql.close()

    if result:
        envs = get_environs()
        loaded_modules.append( args.name )
        print "MOD_SEQ="
        print ",".join( loaded_modules )
        if result[2]:
            envs["PATH"].insert(0, result[2] )
        if result[3]:
            envs["C_INCLUDE_PATH"].insert(0, result[3])
            envs["CPLUS_INCLUDE_PATH"].insert(0, result[3])
        if result[4]:
            envs["LIBRARY_PATH"].insert(0, result[4])
            envs["LD_LIBRARY_PATH"].insert(0, result[4])
            envs["DYLD_LIBRARY_PATH"].insert(0, result[4])

        print_environs(envs)
        print "UNLOADED="
        print_end = True
        if result[5]:
            for each in filter(None, result[5].split(",")):
                if each in loaded_modules:
                    continue
                print each
                print_end = False
        if print_end:
            print "END"
    else:
        print "WRONG_NAME"

def handle_unload(args):
    loaded_modules = filter(None, args.seq.split(","))
    if args.name not in loaded_modules:
        print "NOT_LOADED"
        return
    sql = Sqlite()
    sql.execute("select * from module where name = ?", (args.name, ))
    result = sql.fetchone()
    sql.close()

    if result:
        list_safe_remove(loaded_modules, args.name)
        print "MOD_SEQ="
        print ",".join( loaded_modules )

        envs = get_environs()
        if result[2]:
            remove_path(envs, filter(None, result[2].split(":")))
        if result[3]:
            remove_incs(envs, filter(None, result[3].split(":")))
        if result[4]:
            remove_libs(envs, filter(None, result[4].split(":")))
        print_environs( envs )
    print "END"

def handle_unloaded(args):
    loaded_modules = filter(None, args.seq.split(","))
    sql = Sqlite()
    sql.execute("select name from module")
    names = [name[0] for name in sql.fetchall()]
    sql.close()
    names.sort()
    for each in names:
        if each in loaded_modules:
            continue
        print each

def main(args):
    subcommands = {"avail": handle_avail,
                   "clear": handle_clear,
                   "depend": handle_depend,
                   "info": handle_info,
                   "list": handle_list,
                   "load": handle_load,
                   "unload": handle_unload,
                   "unloaded": handle_unloaded}
    try:
        subcommands[ args.subcmd ]( args )
    except KeyError:
        error_exit("Unknown subcommand {}".format( args.subcmd ))

def parse_argument():
    parser = argparse.ArgumentParser(description="Loonmod core program")
    subparsers = parser.add_subparsers(title="subcommand", dest="subcmd")

    parser_insert = subparsers.add_parser("avail", help="List available modules")
    parser_insert.add_argument("-n", "--name", help="If set, search the modules that have similar names")

    parser_clear = subparsers.add_parser("clear", help="Clear all the loaded modules")
    parser_clear.add_argument("--seq", required=True, help="A sequence of loaded modules (hidden parameter)")

    parser_depend = subparsers.add_parser("depend", help="List the dependencies of the specified module")
    parser_depend.add_argument("-n", "--name", required=True, help="Module name")
    parser_depend.add_argument("--seq", help="A sequence of loaded modules (hidden parameter)")
    parser_depend.add_argument("-D", "--unloaded-dependencies", action="store_true", help="Unloaded dependencies only")

    parser_info = subparsers.add_parser("info", help="Show the info of the module")
    parser_info.add_argument("-n", "--name", required=True, help="Module name")
    parser_info.add_argument("--seq", help="A sequence of loaded modules (hidden parameter)")

    parser_list = subparsers.add_parser("list", help="List loaded modules")
    parser_list.add_argument("-n", "--name", help="If set, list loaded modules that have similar names")
    parser_list.add_argument("--seq", required=True, help="A sequence of loaded modules (hidden parameters)")

    parser_load = subparsers.add_parser("load", help="Load a module")
    parser_load.add_argument("-n", "--name", required=True, help="Module name")
    parser_load.add_argument("--seq", required=True, help="A sequence of loaded modules (hidden parameter)")
    #parser_load.add_argument("-d", "--with-dependencies", action="store_true", help="Also load the dependencies if not loaded")

    parser_unload = subparsers.add_parser("unload", help="Unload a module")
    parser_unload.add_argument("-n", "--name", required=True, help="Module name")
    parser_unload.add_argument("--seq", required=True, help="A sequence of loaded modules (hidden parameters)")

    parser_unloaded = subparsers.add_parser("unloaded", help="List unloaded modules")
    parser_unloaded.add_argument("--seq", required=True, help="A sequence of loaded modules (hidden parameters)")

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_argument()
    main(args)
