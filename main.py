import argparse
import json
from analysis.tracer import Tracer
import analysis.dataservice
from db_conn import DbConn
from scripting.dataservice import DataService
from scripting.node import Builder
from parsing.parser import Parser
from parsing.tokenizer import Tokenizer
from scripting.delete_scripter import DeleteScripter
from scripting.insert_scripter import InsertScripter

def get_sql_connection(db_name) -> DbConn: 
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
    insert_parser.add_argument('-r', '--reference-table', action='append', 
        help='Flag this table as reference data (should use original foreign key instead of copying)', 
        dest='reference_tables')
    insert_parser.add_argument('-t', '--transaction', action='store_true', help='Wrap insert statements in a transaction')

    delete_parser = subparsers.add_parser('delete')    
    delete_parser.add_argument('table_name', help='Name of the table to operate on')
    delete_parser.add_argument('db_name', help='Name of the database to connect to')
    delete_parser.add_argument('id', help='ID of the row to operate on', type=int)
    delete_parser.add_argument('--schema', default='dbo', help='Schema of the table (default: dbo)')
    delete_parser.add_argument('-r', '--reference-table', action='append', 
        help='Flag this table as reference data (should use original foreign key instead of copying)',
        dest='reference_tables')
    delete_parser.add_argument('-t', '--transaction', action='store_true', help='Wrap delete statements in a transaction')

    uppercase_parser = subparsers.add_parser('uppercase')
    uppercase_parser.add_argument('file', help='Input SQL file')
    uppercase_parser.add_argument('-o', '--output', help='Output SQL file (optional)', default=None)

    lowercase_parser = subparsers.add_parser('lowercase')
    lowercase_parser.add_argument('file', help='Input SQL file')
    lowercase_parser.add_argument('-o', '--output', help='Output SQL file (optional)', default=None)

    query_parser = subparsers.add_parser('query')
    query_parser.add_argument('db_name', help='Name of the database to connect to')
    query_parser.add_argument('-t', '--type', help='Type of objects to query. views, procedures, triggers)', choices=['views', 'procedures', 'triggers'])
    query_parser.add_argument('-q', '--query', help='Text to search for in object definitions', default=None)

    trace_parser = subparsers.add_parser('trace')
    trace_parser.add_argument('file', help='Input SQL file')
    trace_parser.add_argument('-c', '--column', help='Column name to trace', default=None)
    trace_parser.add_argument('-i', '--column-index', help='Column index to trace (0-based)', type=int, default=None)
    trace_parser.add_argument('-r', '--result-set', help='Result set number to trace (0-based)', type=int, default=None)
    trace_parser.add_argument('-s', '--connection-string',
        help='Connection string to trace views', 
        default=None,
        dest='connection_string')

    args = parser.parse_args()

    if args.action == 'uppercase':
        tokens = Tokenizer(open(args.file, 'r').read()).parse()
        output = Parser(tokens).parse()
        print(output.uppercase())

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

    elif args.action == 'lowercase':
        tokens = Tokenizer(open(args.file, 'r').read()).parse()
        output = Parser(tokens).parse()
        print(output.lowercase())

    elif args.action in ['insert', 'delete']:
        conn = get_sql_connection(args.db_name)
        node = Builder(DataService(conn), args.reference_tables).build_node(args.schema, args.table_name, args.id)
        lines = (InsertScripter if args.action == 'insert' else DeleteScripter)(node, transaction=args.transaction).script()
        print('\n\n'.join(lines))

    elif args.action == 'trace':
        dataservice = None
        if args.connection_string:
            dataservice = analysis.dataservice.DataService(get_sql_connection(args.connection_string))
        tokens = Tokenizer(open(args.file, 'r').read()).parse()
        parser = Parser(tokens)
        output = parser.parse()
        print(Tracer(output, dataservice).trace(args.column, args.column_index, args.result_set))

if __name__ == "__main__":
    main()