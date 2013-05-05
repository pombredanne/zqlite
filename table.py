#!/usr/bin/env python

from collections import OrderedDict
import os


def main():
    # A demonstration. Run this file from the command line to see it in action.
    # Or just "include table" in your Python scripts and then call table.table() with a list of dicts. 
    import requests, json
    r = requests.get('https://api.scraperwiki.com/api/1.0/datastore/sqlite?format=jsondict&name=gaza&query=select+*+from+features+limit+10')
    test_data = json.loads(r.text)
    print table(test_data)


def table(data):
    # Basic checks that data structure is suitable
    if type(data) is not list:
        raise Exception('Wrong data structure provided. table() requires a List of Dicts. %s provided.' % type(data).__name__.title())
    if len(data) == 0:
        raise Exception('No data provided. table() requires a List of Dicts.')
    if type(data[0]) is not dict and not isinstance(data[0], OrderedDict):
        raise Exception('Wrong data structure provided. table() requires a List of Dicts or OrderedDicts. List of %ss provided.' % type(data[0]).__name__)

    # Extract header info
    col_data = []
    for key in data[0].keys():
        col_data.append({
            'width': chars(prepare(key)) + 2 # add 2 for cell padding
        })

    # Establish default column widths
    for row in data:
        for i, val in enumerate(row.values()):
            col_data[i]['width'] = max(col_data[i]['width'], chars(prepare(val)) + 2)

    max_width = int(os.popen('stty size', 'r').read().split()[1])
    table_width = get_table_width(col_data)

    if table_width > max_width:
        # The table is too wide to fit on the screen!
        # Try trimming characters off the longest cells until it fits
        while table_width > max_width:
            # Find widest column
            widest_column = 0
            widest_column_width = 0
            for i, col in enumerate(col_data):
                if col['width'] > widest_column_width:
                    widest_column = i
                    widest_column_width = col['width']
            # trim widest column
            col_data[widest_column]['width'] -= 1
            # calculate new total width
            table_width = get_table_width(col_data)

    # Right, columns will fit on the screen
    # Start building the table
    output = ''

    # Prepare line - we'll use it three times
    line = '+'
    for col in col_data:
        line += '-' * col['width']
        line += '+'

    # Top line
    output += line

    # Header row
    output += '\n| '
    for i, key in enumerate(data[0].keys()):
        output += pad(prepare(key), col_data[i]['width']-2) # trim extra 2 characters for cell padding
        output += ' | '

    # Header/body divider line
    output += '\n' + line

    # Body rows
    for row in data:
        output += '\n| '
        for i, val in enumerate(row.values()):
            output += pad(prepare(val), col_data[i]['width']-2) # trim extra 2 characters for cell padding
            output += ' | '

    # Bottom line
    output += '\n' + line

    return output


def chars(thing):
    # Count characters in thing
    # Handles integers, floats and unicode characters fine
    if type(thing) is unicode:
        return len(thing.decode('utf-8'))
    if thing is None:
        # str(None) would return 'None'. We can do better.
        return 0
    else:
        # some other type: try turning it into a string.
        return len(str(thing))


def prepare(thing):
    # Strip whitespace from strings (because newlines/tabs will break our table)
    if type(thing) is unicode or type(thing) is str:
        return thing.strip()
    if thing is None:
        thing = ''
    return thing


def pad(thing, width):
    # Uses Python 2.5+ format specification language
    # to pad and align a string within a set space
    if type(thing) is int or type(thing) is float:
        template = '{0: >%s}' % width
    else:
        template = '{0: <%s}' % width
    t = (template).format(thing)
    # Trim it down if it's too long
    if len(t) > width:
        t = t[:width-1] + u"\u2026"
    return t


def get_table_width(col_data):
    # col_data should be a list of dicts, each with a "width" key
    total_width = 1 # Start at 1, because table left border takes up one character
    for col in col_data:
        total_width += col['width']
        total_width += 1 # Add 1 for column right border
    total_width += 1 # Add 1 for newline character after each row!!
    return total_width


if __name__ == '__main__':
    main()
