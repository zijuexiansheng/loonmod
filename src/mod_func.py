#!/usr/bin/env python2

import sys
import os
import argparse
import sqlite3
import json

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

def get_items(seq_names, attr):
    ret = []
    sql = Sqlite()
    for name in seq_names:
        sql.execute("select %s from module where name = ?" % attr, (name, ))
        res = sql.fetchone()
        if res and res[0]:
            ret += filter(None, json.loads(res[0]))
    sql.close()
    return ret

env_strings = ["PATH", "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH", "LIBRARY_PATH", "LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH"]

def get_environs():
    global env_strings
    ret = {}
    for each in env_strings:
        ret[ each ] = filter(None, os.environ.get( each, "" ).split(":"))
    return ret

def stringfy_environs(envs):
    global env_strings
    for each in env_strings:
        envs[each] = ":".join( envs[each] )
    return envs

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
    seq = json.loads( args.seq )
    if seq:
        seq_names = seq.keys()
        paths = get_items(seq_names, "path")
        incs = get_items(seq_names, "inc")
        libs = get_items(seq_names, "lib")

        envs = get_environs()
        remove_path(envs, paths)
        remove_incs(envs, incs)
        remove_libs(envs, libs)
        print json.dumps( stringfy_environs(envs) )
    print "{}"

def handle_depend(args):
    dep = get_items([args.name], "dependency")
    if dep:
        if args.unloaded_dependencies:
            if args.seq == None:
                error_exit("--seq is required")
            mod_seq = json.loads(args.seq)
            printed = False
            for each in dep:
                if not mod_seq.has_key( each )
                    print each
                    printed = True
            if not printed:
                print '\n'
        else:
            print "\n".join( dep )            
    else:
        print "\n"

def print_json_list(msg, json_list):
    print msg
    for each in json.loads(json_list):
        print "\t* [{}]".format(each)

def handle_info(args):
    sql = Sqlite()
    sql.execute("select * from module where name = ?", (args.name, ))
    result = sql.fetchone()
    sql.close()

    if result:
        print "Info for module [args]"
        print "module name: [{}]".format( result[1] )
        print_json_list("module bin paths:", result[2])
        if result[3]:
            print_json_list("module include paths:", result[3])
        if result[4]:
            print_json_list("module library path:", result[4])
        if result[5]:
            if args.seq == None:
                print "module dependencies:"
                for each in filter(None, json.loads(result[5])):
                    print "\t* [{}]".format( each )
            else:
                print "module dependencies (mark loaded):"
                loaded_modules = json.loads(args.seq)
                for each in filter(None, json.loads(result[5])):
                    if loaded_modules.has_key( each ):
                        print "\t* [{}]    (loaded)".format( each )
                    else:
                        print "\t* [{}]".format( each )
    else:
        error_exit("Module [{}] doesn't exist".format( args.name ))

def handle_list(args):
    loaded_modules = json.loads(args.seq))
    if args.name:
        for each in loaded_modules.iterkeys():
            if each.find( args.name ) != -1:
                print each
    else:
        print "\n".join( loaded_modules.keys() )

def handle_load(args):
    ret_str = {}
    loaded_modules = json.loads( args.seq )
    this_module = loaded_modules.get(args.name)
    if this_module:
        if this_module["type"] == 'U':
            ret_str["retval"] = "LOADED"
            print json.dumps( ret_str )
            return
        elif this_module['type'] == 'D':
            this_module['type'] = 'U'

            ret_str["retval"] = "UPGRADED"
            ret_str["seq"] = json.dumps( loaded_modules )
            print json.dumps( ret_str )

            sys.stderr.write("[DEBUG]: change 'D' type module [{}] to 'U' type\n".format(args.name))
            return
        else:
            ret_str["retval"] = "UNKNOWN_TYPE"
            print json.dumps( ret_str )
            return
    sql = Sqlite()
    sql.execute("select * from module where name = ?", (args.name, ))
    result = sql.fetchone()

    if result:
        deps = json.loads( result[5] ) if result[5] else []
        loaded_modules[ args.name ] = {"type": "U", "deps": deps}

        sys.stderr.write("[DEBUG]: load 'U' type module [{}]\n".format(args.name))

        unresolved_deps = set()
        for each in deps:
            if not loaded_modules.has_key( each )
                unresolved_deps.add( each )
        tmp_path = json.loads( result[2] ) if result[2] else []
        tmp_inc = json.loads( result[3] )  if result[3] else []
        tmp_lib = json.loads( result[4] )  if result[4] else []

        envs = get_environs()
        while len(unresolved_deps) > 0:
            cur_name = unresolved_deps.pop()
            sql.execute("select * from module where name = ?", (cur_name, ))
            result = sql.fetchone()
            deps = json.loads( result[5] ) if result[5] else []
            loaded_modules[ cur_name ] = {"type": "D", "deps": deps}
            sys.stderr.write("[DEBUG]: load 'D' type module [{}]\n".format( cur_name ))

            for each in deps:
                if loaded_modules.has_key(each) or each in unresolved_deps:
                    continue
                unresolved_deps.add(each)
            if result[2]:
                tmp_path.extend( json.loads(result[2]) )
            if result[3]:
                tmp_inc.extend( json.loads(result[3]) )
            if result[4]:
                tmp_lib.extend( json.loads(result[4]) )
            
        if tmp_path:
            envs["PATH"]                = tmp_path + envs["PATH"]
        if tmp_inc:
            envs["C_INCLUDE_PATH"]      = tmp_inc + envs["C_INCLUDE_PATH"]
            envs["CPLUS_INCLUDE_PATH"]  = tmp_inc + envs["CPLUS_INCLUDE_PATH"]
        if tmp_lib:
            envs["LIBRARY_PATH"]        = tmp_lib + envs["LIBRARY_PATH"]
            envs["LD_LIBRARY_PATH"]     = tmp_lib + envs["LD_LIBRARY_PATH"]
            envs["DYLD_LIBRARY_PATH"]   = tmp_lib + envs["DYLD_LIBRARY_PATH"]

        ret_str = stringfy_environs(envs)
        ret_str['seq'] = json.dumps(loaded_modules)
        ret_str["retval"] = "GOOD"
        print json.dumps( ret_str )
    else:
        ret_str["retval"] = "WRONG_NAME"
        print json.dumps( ret_str )
    sql.close()

def build_graph(loaded_modules, root):
    G = {}
    unvisited_nodes = set()
    unvisited_nodes.add(root)
    while len(unvisited_nodes) > 0:
        node = unvisited_nodes.pop()
        G[ node ] = filter(lambda x: loaded_modules[x]['type'] != 'U', loaded_modules[ node ]['deps'])
        unvisited_nodes |= set( G[ node ] ) - set( G.keys() )
    return G

def remove_nodes(graph, loaded_module, root):
    did_remove = False
    if len(graph) <= 1:
        return False

    new_nodes = filter(lambda x: not graph.has_key(x), loaded_module.iterkeys())
    while len(new_nodes) > 0 and len(graph) > 1:
        tail_node = new_nodes.pop()
        for each_dep in loaded_module[ tail_node ]['deps']:
            if each_dep != root and graph.has_key(each_dep):
                new_nodes.append( each_dep )
                graph.pop( each_dep )
                did_remove = True

    if did_remove and len(graph) > 1:
        reached_nodes = set()
        node_queue = set()
        node_queue.add( root )
        while len(node_queue) > 0:
            node = node_queue.pop()
            reached_nodes.add( node )
            for each_node in graph[ node ]:
                if graph.has_key(each_node) and each_node not in reached_nodes:
                    node_queue.add( each_node )
        for node in graph.keys():
            if node not in reached_nodes:
                graph.pop( node )
            else:
                graph[node] = filter(lambda x: x in reached_nodes, graph[node])
    return did_remove

def handle_unload(args):
    ret_str = {}
    loaded_modules = json.loads( args.seq )
    this_module = loaded_modules.get( args.name )
    if this_module:
        graph = build_graph( loaded_modules, args.name )
        
        while remove_nodes(graph, loaded_modules, args.name):
            pass

        sql = Sqlite()
        envs = get_environs()
        for module_name in graph.iterkeys():
            sys.stderr.write("[DEBUG]: unload '{}' type module [{}]\n".format(loaded_modules[module_name]['type'], module_name))
            loaded_modules.pop( module_name )
            sql.execute("select * from module where name = ?", (module_name, ))
            result = sql.fetchone()
            if result[2]:
                remove_path(envs, filter(None, json.loads(result[2])))
            if result[3]:
                remove_incs(envs, filter(None, json.loads(result[3])))
            if result[4]:
                remove_libs(envs, filter(None, json.loads(result[4])))
        sql.close()
        ret_str = stringfy_environs(envs)
        ret_str["seq"] = json.dumps( loaded_modules )

        show_warning = False
        for deps in loaded_modules.itervalues():
            if args.name in deps:
                show_warning = True
                break
        if show_warning:
            ret_str['retval'] = 'SHOW_WARNING'
        else:
            ret_str['retval'] = "GOOD"
        print json.dumps( ret_str )

    else:
        ret_str["retval"] = "NOT_LOADED"
        print json.dumps( ret_str )

def handle_unloaded(args):
    loaded_modules = json.loads( args.seq )
    sql = Sqlite()
    sql.execute("select name from module")
    names = [name[0] for name in sql.fetchall()]
    sql.close()
    names.sort()
    for each in names:
        if loaded_modules.has_key( each ):
            continue
        print each

def handle_parsereturn(args):
    retstr = json.loads(args.retstr)
    print retstr.get(args.keyword, "")

def main(args):
    subcommands = {"avail": handle_avail,
                   "clear": handle_clear,
                   "depend": handle_depend,
                   "info": handle_info,
                   "list": handle_list,
                   "load": handle_load,
                   "unload": handle_unload,
                   "unloaded": handle_unloaded,
                   "parsereturn": handle_parsereturn}
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

    parser_parsereturn = subparser.add_parser("parsereturn", help="Parse one field of the return string")
    parser_parsereturn.add_argument("retstr", help="The return string to be parsed")
    parser_parsereturn.add_argument("keyword", metavar="keyword", choices=["seq", "path", "c_include_path", "cplus_include_path", "library_path", "ld_library_path", "dyld_library_path", "retval"], help="The keyword to be parsed")

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_argument()
    main(args)
