#!/usr/bin/env python

import os, sys
import readline
import rlcompleter
import sqlite3
import table # this is table.py, in the current directory
from collections import OrderedDict


# Enable tab completion under Mac OS X
# See: http://stackoverflow.com/questions/7116038/
if 'libedit' in readline.__doc__:
    readline.parse_and_bind("bind ^I rl_complete")
else:
    readline.parse_and_bind("tab: complete")


usage = """Enter an interactive SQLite shell:
$ ./zqlite.py [database-file]

Type ^D, "exit" or "quit" to leave shell.
"""

shell_help = '''
show tables             show all tables, views and indices
describe [table-name]   show columns in a table
exit / quit / q / ^D    leave the zqlite shell
'''

db_file = None
suggestions_first = set(['create','delete','drop','insert','select','update','help','describe','quit','exit','show tables'])
suggestions_later = set(['sqlite_master'])


def main():
    args = sys.argv[1:]

    if len(args) == 1:
        if not os.path.isfile(args[0]):
            print >> sys.stderr, "%s is not a valid file path" % args[0]
            print ''
            print usage
            exit()
        global db_file
        db_file = args[0]
    else:
        print usage
        exit()

    # Valid file supplied! Let's show them what's in it.
    print database_overview()

    # Populate the tab completion suggestions array
    table_names = execute_command("select name from sqlite_master where type in ('table', 'view');")
    if table_names:
        for table_name in table_names:
            suggestions_later.update([table_name['name']])
            first_row = execute_command("""select * from "%s" limit 1;""" % table_name['name'])
            if first_row:
                suggestions_later.update(first_row[0].keys())

    enter_shell()


def enter_shell():
    previous_command_was_control_c = False
    readline.set_completer(completer)

    while True:
        try:
            a = raw_input("> ")
        except KeyboardInterrupt, e:
            # Allow user to ^C for a new console line
            # Or ^C twice in a row to quit
            if previous_command_was_control_c:
                leave_shell()
            else:
                previous_command_was_control_c = True
                sys.stdout.write('^C\n')
        except EOFError, e:
            # Allow user to ^D out of the console`
            leave_shell()
        else:
            # Reset the ^C history monitor
            previous_command_was_control_c = False

            if a.strip().lower() in ['exit','.exit','quit','q']:
                exit()
            elif a.strip().lower().startswith('show tables'):
                print database_overview()
            elif a.strip().lower().startswith('help'):
                print shell_help
            elif a.strip().lower().startswith('describe'):
                try:
                    table_name = a.strip().lower().split()[1]
                except IndexError, e:
                    print 'Which table would you like to describe?'
                else:
                    print table_overview(table_name)
            else:
                result = execute_command(a)
                if isinstance(result, list) and len(result):
                    print table.table(result)


def execute_command(command):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    try:
        result = cursor.execute(command)
    except sqlite3.OperationalError, e:
        print 'Invalid query'
        print e
        return False
    else:
        c = command.lower().strip()
        if result.description:
            column_names = [ col[0] for col in result.description ]
            rows = []
            for row in result:
                temp_row = OrderedDict()
                for i, cell in enumerate(row):
                    temp_row[column_names[i]] = cell
                rows.append(temp_row)
            return rows
        else:
            return None

    conn.commit()
    conn.close()


def database_overview():
    result = execute_command("select type, name, sql from sqlite_master;")
    if result:
        for thing in result:
            if thing['type'] in ['table', 'view']:
                r2 = execute_command("""select count(*) as n from "%s";""" % thing['name'])
                thing['rows'] = int(r2[0]['n'])
            else:
                thing['rows'] = None
        return table.table(result)


def table_overview(table_name):
    result = execute_command("""select * from "%s" limit 1;""" % table_name)
    overview = []
    if result:
        for col_name, example_value in result[0].iteritems():
            row = OrderedDict()
            row['Column name'] = col_name
            row['Example value'] = example_value
            overview.append(row)
        return table.table(overview)


def completer(text, state):
    # Readline calls this function repeatedly, incrementing the "state" integer,
    # until it returns None. It then uses all previously returned values
    # as possible strings for autocompletion.

    # So, we create a list of possible completions (based on "text" the user
    # has already typed) and return each one in turn, until there are no more.

    if len(readline.get_line_buffer().split()) < 2:
        suggestions = suggestions_first
    else:
        suggestions = suggestions_later

    options = [i+' ' for i in suggestions if i.startswith(text)]
    if state < len(options):
        return options[state]
    else:
        return None


def leave_shell():
    sys.stdout.write('\n')
    exit()


if __name__ == "__main__":
    main()
