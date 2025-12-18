import argparse
import json
from dataservice import DataService
from node import Builder
from parsing.parser import Parser
from parsing.tokenizer import Tokenizer
from scripter import DeleteScripter, InsertScripter

def get_sql_connection(db_name): 
    import pyodbc
    # Read connection string from file
    with open('connection_string.json', 'r') as f:
        data = json.loads(f.read())
    conn_str = data[db_name].strip()
    # Return pyodbc connection
    return pyodbc.connect(conn_str)

def main():
    parser = argparse.ArgumentParser(description='Generate SQL scripts for inserting or deleting rows with related data.')
    subparsers = parser.add_subparsers(dest='action')

    insert_parser = subparsers.add_parser('insert')
    insert_parser.add_argument('table_name', help='Name of the table to operate on')
    insert_parser.add_argument('db_name', help='Name of the database to connect to')
    insert_parser.add_argument('id', help='ID of the row to operate on', type=int)
    insert_parser.add_argument('--schema', default='dbo', help='Schema of the table (default: dbo)')
    insert_parser.add_argument('-f', '--foreign-key', action='append', help='Copy row referenced by foreign key', dest='foreign_keys')
    insert_parser.add_argument('-t', '--transaction', action='store_true', help='Wrap insert statements in a transaction')

    delete_parser = subparsers.add_parser('delete')    
    delete_parser.add_argument('table_name', help='Name of the table to operate on')
    delete_parser.add_argument('db_name', help='Name of the database to connect to')
    delete_parser.add_argument('id', help='ID of the row to operate on', type=int)
    delete_parser.add_argument('--schema', default='dbo', help='Schema of the table (default: dbo)')
    delete_parser.add_argument('-f', '--foreign-key', action='append', help='Copy row referenced by foreign key', dest='foreign_keys')
    delete_parser.add_argument('-t', '--transaction', action='store_true', help='Wrap delete statements in a transaction')

    uppercase_parser = subparsers.add_parser('uppercase')
    uppercase_parser.add_argument('file', help='Input SQL file')
    uppercase_parser.add_argument('-o', '--output', help='Output SQL file (optional)', default=None)

    query_parser = subparsers.add_parser('query')
    query_parser.add_argument('db_name', help='Name of the database to connect to')
    query_parser.add_argument('-t', '--type', help='Type of objects to query. views, procedures, triggers)', choices=['views', 'procedures', 'triggers'])
    query_parser.add_argument('-q', '--query', help='Text to search for in object definitions', default=None)

    args = parser.parse_args()
    if args.action == 'uppercase':
        tokens = Tokenizer(open(args.file, 'r').read()).parse()
        output = Parser(tokens).parse()
        print(''.join(map(str, output)))
    elif args.action == 'query':
        conn = get_sql_connection(args.db_name)
        from queries import Queryer
        queryer = Queryer(conn)
        results = []
        if args.type is None:
            results.extend(queryer.views(args.query))
            results.extend(queryer.procedures(args.query))
            results.extend(queryer.triggers(args.query))
        elif args.type == 'views':
            results = queryer.views(args.text)
        elif args.type == 'procedures':
            results = queryer.procedures(args.text)
        elif args.type == 'triggers':
            results = queryer.triggers(args.text)
        for _, definition in results:
            print(definition.replace('\r\n', '\n'))
    else:
        conn = get_sql_connection(args.db_name)
        node = Builder(DataService(conn), args.foreign_keys).build_node(args.schema, args.table_name, args.id)
        lines = (InsertScripter if args.action == 'insert' else DeleteScripter)(node, transaction=args.transaction).script()
        print('\n\n'.join(lines))

if __name__ == "__main__":
    main()