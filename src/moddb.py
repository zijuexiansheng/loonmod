#!/usr/bin/env python2

import sys
import os
import argparse
import sqlite3

dirname = os.path.join( os.environ['LOONCONFIG'], "loonmod" )

class Sqlite:
    def __init__(self):
        os.system("mkdir -p {}".format( dirname ))
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
    sys.stderr.write(msg)
    sys.stderr.write('\n')
    sys.exit( exit_code )

def check_dependency(sql, dependency):
    for each in dependency:
        sql.execute("select name from module where name = ?", (each, ))
        if sql.fetchone():
            continue
        else:
            sql.close()
            error_exit("Error: Dependency [%s] doesn't exist. Please check the format, all the dependencies should be comma delimited." % each)

def insert_mod(name, path = None, inc = None, lib = None, dependency = None, additional_path = None):
    print "Insert module [%s]" % name
    sql = Sqlite()

    stmt = "insert into module (%s) values (%s)"
    insertion_options = ['name', 'path']
    if additional_path:
        params = [name, path + ":" + ":".join( additional_path )]
    else:
        params = [name, path]
    if inc:
        insertion_options.append('inc')
        params.append(":".join(inc))
    if lib:
        insertion_options.append('lib')
        params.append(":".join(lib))
    if dependency:
        check_dependency( sql, dependency )
        insertion_options.append('dependency')
        params.append(",".join(dependency))

    try:
        sql.execute(stmt % (", ".join(insertion_options), ", ".join(["?" for each in insertion_options])), tuple(params))
        sql.commit()
        print "Done!"
    except sqlite3.IntegrityError as e:
        print e
    sql.close()

def handle_insert(args):
    insert_mod(args.name, args.path, args.include, args.lib, args.dependency, args.additional_path)

def check_depended(name, sql):
    sql.execute("select name, dependency from module where dependency like '%%%s%%'" % name)
    names = []
    for each in sql.fetchall():
        dep = filter(None, each[1].split(','))
        if name in dep:
            names.append( each[0] )
    if names:
        sql.close()
        names.sort()
        sys.stderr.write("Error: The following modules depends on [%s]\n" % name)
        os.system("echo \"%s\" | column" % "\n".join(names))
        sys.exit(1)

def delete_mod(name):
    print "Delete module [%s]" % name
    sql = Sqlite()

    check_depended(name, sql)

    sql.execute("delete from module where name = ?", (name, ))
    sql.commit()
    sql.close()
    print "Done!"

def handle_delete(args):
    delete_mod(args.name)

def update_mod(name, path = None, inc = None, lib = None, dependency = None, clear_inc = False, clear_lib = False, clear_dependency = False):
    if clear_inc and inc:
        error_exit("Error: -i and -I cannot be set simultaneously!")
    if clear_lib and lib:
        error_exit("Error: -l and -L cannot be set simultaneously!")
    if clear_dependency and dependency:
        error_exit("Error: -d and -D cannot be set simultaneously!")
    print "Update module [%s]" % name
    sql = Sqlite()

    stmt = "update module set %s where name = ?"
    insertion_options = []
    params = []

    if path:
        insertion_options.append("path = ?")
        params.append( ":".join(path) )
    if inc:
        insertion_options.append("inc = ?")
        params.append( ":".join(inc) )
    if lib:
        insertion_options.append("lib = ?")
        params.append( ":".join(lib) )
    if dependency:
        check_dependency(sql, dependency)
        insertion_options.append("dependency = ?")
        params.append( ",".join(dependency) )
    if clear_inc:
        insertion_options.append("inc = NULL")
    if clear_lib:
        insertion_options.append("lib = NULL")
    if clear_dependency:
        insertion_options.append("dependency = NULL")

    if params:
        params.append(name)
    else:
        error_exit("Error: please set parameters that are to be updated!")
    
    try:
        sql.execute(stmt % ", ".join(insertion_options), tuple(params))
        sql.commit()
        print "Done!"
    except sqlite3.IntegrityError as e:
        raise
    sql.close()
        

def handle_update(args):
    update_mod(args.name, args.path, args.include, args.lib, args.dependency, args.Include, args.Lib, args.Dependency)

def show_all_mod():
    print "List all module names:"
    sql = Sqlite()
    sql.execute("select name from module")
    names = [name[0] for name in sql.fetchall()]
    sql.close()
    names.sort()
    os.system("echo \"%s\" | column" % "\n".join(names))

def show_mod(name):
    print "Show info for module [%s]:" % name
    sql = Sqlite()
    sql.execute("select * from module where name = ?", (name, ))
    result = sql.fetchone()
    sql.close()

    if result:
        print "module ID: [%d]" % result[0]
        print "module name: [%s]" % result[1]
        print "module bin path: [%s]" % result[2]
        if result[3]:
            print "module include path: [%s]" % result[3]
        if result[4]:
            print "module library path: [%s]" % result[4]
        if result[5]:
            print "module dependencies:"
            for each in result[5].split(","):
                print "\t* [%s]" % each
    else:
        print "Module [%s] doesn't exist" % name

def handle_list(args):
    if args.all:
        show_all_mod()
    if args.name:
        show_mod(args.name)

def create_table():
    print "Create database for modules"
    sql = Sqlite()
    try:
        sql.execute("""create table module(
            id integer primary key autoincrement,
            name text unique,
            path text not null,
            inc text,
            lib text,
            dependency text
        )""")
        sql.commit()
        print "Done!"
    except sqlite3.OperationalError as e:
        print e
    sql.close()

def clear_table():
    print "Clear table"
    sql = Sqlite()
    try:
        sql.execute("delete from module")
        sql.commit()
        print "Done!"
    except sqlite3.OperationalError as e:
        print e
    sql.close()

def handle_db(args):
    if args.operation == 'create':
        create_table()
    elif args.operation == 'cls':
        clear_table()
    else:
        error_exit("Error: Unknown database operation [%s]" % args.operation)

def parse_argument():
    parser = argparse.ArgumentParser(description="Loonmod database management core")
    subparsers = parser.add_subparsers(title="functionalities", dest="func")

    parser_insert = subparsers.add_parser('insert', help='insert a module into database')
    parser_insert.add_argument(type=str, dest='name', metavar='name', help="module name")
    parser_insert.add_argument(type=str, dest='path', metavar='path', help="bin path of the module")
    parser_insert.add_argument('-i', type=str, dest='include', metavar='include', action="append", help="include path of the module (repeat use)")
    parser_insert.add_argument('-l', type=str, dest='lib', metavar='lib', action="append", help="library path of the module (repeat use)")
    parser_insert.add_argument('-d', type=str, dest='dependency', metavar='dependency', action="append", help="dependency of the module (repeat use)")
    parser_insert.add_argument("-p", type=str, dest="additional_path", metavar="additional_path", action="append", help="additional path (repeat use)")

    parser_delete = subparsers.add_parser('delete', help='delete a module from the database')
    parser_delete.add_argument(type=str, dest='name', metavar='name', help="module name")

    parser_update = subparsers.add_parser('update', help='update a module')
    parser_update.add_argument(type=str, dest='name', metavar='name', help="module name")
    parser_update.add_argument('-p', type=str, dest='path', metavar='path', action="append", help="bin path of the module (repeat use)")
    parser_update.add_argument('-i', type=str, dest='include', metavar='include', action="append", help="include path of the module (repeat use)")
    parser_update.add_argument('-l', type=str, dest='lib', metavar='lib', action="append", help="library path of the module (repeat use)")
    parser_update.add_argument('-d', type=str, dest='dependency', metavar='dependency', action="append", help="dependency of the module (repeat use)")
    parser_update.add_argument('-I', dest='Include', action='store_true', help="clear include path of the module")
    parser_update.add_argument('-L', dest='Lib', action='store_true', help="clear library path of the module")
    parser_update.add_argument('-D', dest='Dependency', action='store_true', help="clear dependencies of the module")

    parser_list = subparsers.add_parser('list', help="list module(s)")
    parser_list.add_argument('-a', dest='all', action='store_true', help='Show the names of all modules')
    parser_list.add_argument('-n', dest='name', type=str, metavar='name', help="show detailed information of the module")

    parser_db = subparsers.add_parser('db', help="database managements")
    parser_db.add_argument('operation', metavar="operation",choices=["create", "cls"], help='one of database operations from [create, cls]')

    return parser.parse_args()

def main(args):
    if args.func == 'insert':
        handle_insert(args)
    elif args.func == 'delete':
        handle_delete(args)
    elif args.func == 'update':
        handle_update(args)
    elif args.func == 'list':
        handle_list(args)
    elif args.func == 'db':
        handle_db(args)
    else:
        error_exit("Error: Unknown functionality [%s]" % args.func)

if __name__ == '__main__':
    args = parse_argument()
    main(args)
    
