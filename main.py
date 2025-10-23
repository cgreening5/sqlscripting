import argparse

from dataservice import DataService
from node import Builder
from parsing.parser import Parser
from parsing.tokenizer import Tokenizer
from scripter import DeleteScripter, InsertScripter

def get_sql_connection():
    import pyodbc
    # Read connection string from file
    with open('connection_string.txt', 'r') as f:
        conn_str = f.read().strip()
    # Return pyodbc connection
    return pyodbc.connect(conn_str)

def main():
    parser = argparse.ArgumentParser(description='Generate SQL scripts for inserting or deleting rows with related data.')
    subparsers = parser.add_subparsers(dest='action')

    insert_parser = subparsers.add_parser('insert')
    insert_parser.add_argument('table_name', help='Name of the table to operate on')
    insert_parser.add_argument('id', help='ID of the row to operate on')
    insert_parser.add_argument('--schema', default='dbo', help='Schema of the table (default: dbo)')
    insert_parser.add_argument('-f', '--foreign-key', action='append', help='Copy row referenced by foreign key', dest='foreign_keys')

    delete_parser = subparsers.add_parser('delete')    
    delete_parser.add_argument('table_name', help='Name of the table to operate on')
    delete_parser.add_argument('id', help='ID of the row to operate on')
    delete_parser.add_argument('--schema', default='dbo', help='Schema of the table (default: dbo)')
    delete_parser.add_argument('-f', '--foreign-key', action='append', help='Copy row referenced by foreign key', dest='foreign_keys')

    uppercase_parser = subparsers.add_parser('uppercase')
    uppercase_parser.add_argument('file', help='Input SQL file')
    uppercase_parser.add_argument('-o', '--output', help='Output SQL file (optional)', default=None)

    args = parser.parse_args()
    if args.action == 'uppercase':
        tokens = Tokenizer(open(args.file, 'r').read()).parse()
        output = Parser(tokens).parse()
        print(''.join(map(str, output)))
    else:
        conn = get_sql_connection()
        node = Builder(DataService(conn), args.foreign_keys).build_node(args.schema, args.table_name, args.id)
        lines = (InsertScripter if args.action == 'insert' else DeleteScripter)(node).script()
        print('\n\n'.join(lines))

if __name__ == "__main__":
    main()