import pyodbc
import sys
import argparse

from dataservice import DataService
from node import Builder
from scripter import Scripter

def get_sql_connection():
    # Read connection string from file
    with open('connection_string.txt', 'r') as f:
        conn_str = f.read().strip()
    # Return pyodbc connection
    return pyodbc.connect(conn_str)

def main():
    parser = argparse.ArgumentParser(description='Generate SQL scripts for inserting or deleting rows with related data.')
    parser.add_argument('action', choices=['insert', 'delete'], help='Action to perform: insert or delete')
    parser.add_argument('table_name', help='Name of the table to operate on')   
    parser.add_argument('id', help='ID of the row to operate on')
    parser.add_argument('--schema', default='dbo', help='Schema of the table (default: dbo)')
    parser.add_argument('-f', '--foreign-key', action='append', help='Copy row referenced by foreign key', dest='foreign_keys')
    args = parser.parse_args()
    conn = get_sql_connection()
    node = Builder(DataService(conn), args.foreign_keys).build_node(args.schema, args.table_name, args.id)
    lines = Scripter(node).script()
    print('\n\n'.join(lines))

if __name__ == "__main__":
    main()