import pyodbc
import sys
import argparse

def get_sql_connection():
    # Read connection string from file
    with open('connection_string.txt', 'r') as f:
        conn_str = f.read().strip()
    # Return pyodbc connection
    return pyodbc.connect(conn_str)

def script_insert(table_name, id, conn, schema='dbo', fk_value_map=None, identity_var=None):
    cursor = conn.cursor()
    # Get primary key identity column
    cursor.execute(f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ? AND COLUMNPROPERTY(object_id('[{schema}].[{table_name}]'), COLUMN_NAME, 'IsIdentity') = 1
    """, table_name)
    cols = cursor.fetchone()
    if cols is None:
        raise Exception("Unable to find identity column for table " + table_name)
    identity_col = cols[0]

    # Get non-identity, non-generated, non-period columns
    cursor.execute(f"""
        SELECT c.COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN sys.columns sc ON sc.object_id = object_id('[{schema}].[{table_name}]') AND sc.name = c.COLUMN_NAME
        WHERE c.TABLE_NAME = ?
          AND COLUMNPROPERTY(object_id('[{schema}].[{table_name}]'), c.COLUMN_NAME, 'IsIdentity') = 0
          AND (sc.is_computed = 0 OR sc.is_computed IS NULL)
          AND (sc.is_hidden = 0 OR sc.is_hidden IS NULL)
        ORDER BY c.ORDINAL_POSITION
    """, table_name)
    columns = [row[0] for row in cursor.fetchall()]

    # Get row by identity column
    cursor.execute(f"""
        SELECT {', '.join(columns)}
        FROM [{schema}].[{table_name}]
        WHERE {identity_col} = ?
    """, id)
    row = cursor.fetchone()
    if not row:
        return None, None, None

    # Prepare values for insert
    values = []
    for idx, col in enumerate(columns):
        val = row[idx]
        # If this column is a foreign key and we have a mapped value, use it
        if fk_value_map and col in fk_value_map:
            val = fk_value_map[col]
        # Do not quote variable references
        if isinstance(val, str) and isinstance(fk_value_map, dict) and col in fk_value_map and str(val).startswith('@'):
            values.append(str(val))
        elif val is None:
            values.append('NULL')
        elif isinstance(val, str):
            values.append(f"'{val.replace("'", "''")}'")
        elif isinstance(val, bool):
            values.append('1' if val else '0')
        else:
            values.append(str(val))

    # Build insert statement
    insert_sql = f"INSERT INTO [{schema}].[{table_name}] (\n\t{',\n\t'.join(columns)})\n VALUES (\n\t{',\n\t'.join(values)}\n);"
    # If identity_var is provided, set it after insert
    if identity_var:
        insert_sql += f"\nDECLARE @{identity_var} INT = SCOPE_IDENTITY();"
    else:
        identity_var = f"{table_name}_id_{id}"
        insert_sql += f"\nDECLARE @{identity_var} INT = SCOPE_IDENTITY();"
    return insert_sql, identity_col, identity_var

def script_insert_with_related(table_name, id, conn, visited=None, schema='dbo', fk_value_map=None, identity_var=None, script_list=None):
    if visited is None:
        visited = set()
    if script_list is None:
        script_list = []
    key = (schema, table_name, id)
    if key in visited:
        return script_list
    visited.add(key)

    # Insert for the main row
    insert_sql, identity_col, identity_var = script_insert(
        table_name, id, conn, schema=schema, fk_value_map=fk_value_map, identity_var=identity_var
    )
    if insert_sql:
        script_list.append(insert_sql)

    cursor = conn.cursor()
    # Find referencing tables and columns
    cursor.execute(f"""
        SELECT fk_schema.name AS referencing_schema, fk_tab.name AS referencing_table, fk_col.name AS referencing_column
        FROM sys.foreign_key_columns fkc
        INNER JOIN sys.tables pk_tab ON pk_tab.object_id = fkc.referenced_object_id
        INNER JOIN sys.columns pk_col ON pk_col.column_id = fkc.referenced_column_id AND pk_col.object_id = pk_tab.object_id
        INNER JOIN sys.tables fk_tab ON fk_tab.object_id = fkc.parent_object_id
        INNER JOIN sys.columns fk_col ON fk_col.column_id = fkc.parent_column_id AND fk_col.object_id = fk_tab.object_id
        INNER JOIN sys.schemas fk_schema ON fk_schema.schema_id = fk_tab.schema_id
        WHERE pk_tab.name = ?
    """, table_name)
    referencing = cursor.fetchall()

    for ref_schema, ref_table, ref_column in referencing:
        # Find rows in referencing table that point to this id
        cursor.execute(f"""
            SELECT {ref_column}
            FROM [{ref_schema}].[{ref_table}]
            WHERE {ref_column} = ?
        """, id)
        rows = cursor.fetchall()
        for row in rows:
            ref_id = row[0]
            # For referencing table, set its FK column to use the identity variable from parent
            fk_map = {ref_column: f"@{identity_var}"}
            script_insert_with_related(
                ref_table, ref_id, conn, visited, schema=ref_schema,
                fk_value_map=fk_map, identity_var=None, script_list=script_list
            )
    return script_list

def script_delete_with_related(table_name, id, conn, schema='dbo', visited=None, script_list=None):
    if visited is None:
        visited = set()
    if script_list is None:
        script_list = []
    key = (schema, table_name, id)
    if key in visited:
        return script_list
    visited.add(key)

    cursor = conn.cursor()
    # Get primary key identity column
    cursor.execute(f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ? AND COLUMNPROPERTY(object_id('[{schema}].[{table_name}]'), COLUMN_NAME, 'IsIdentity') = 1
    """, table_name)
    cols = cursor.fetchone()
    if cols is None:
        raise Exception("Unable to find identity column for table " + table_name)
    identity_col = cols[0]

    # Find referencing tables and columns
    cursor.execute(f"""
        SELECT fk_schema.name AS referencing_schema, fk_tab.name AS referencing_table, fk_col.name AS referencing_column
        FROM sys.foreign_key_columns fkc
        INNER JOIN sys.tables pk_tab ON pk_tab.object_id = fkc.referenced_object_id
        INNER JOIN sys.columns pk_col ON pk_col.column_id = fkc.referenced_column_id AND pk_col.object_id = pk_tab.object_id
        INNER JOIN sys.tables fk_tab ON fk_tab.object_id = fkc.parent_object_id
        INNER JOIN sys.columns fk_col ON fk_col.column_id = fkc.parent_column_id AND fk_col.object_id = fk_tab.object_id
        INNER JOIN sys.schemas fk_schema ON fk_schema.schema_id = fk_tab.schema_id
        WHERE pk_tab.name = ?
    """, table_name)
    referencing = cursor.fetchall()

    for ref_schema, ref_table, ref_column in referencing:
        # Find rows in referencing table that point to this id
        cursor.execute(f"""
            SELECT {ref_column}
            FROM [{ref_schema}].[{ref_table}]
            WHERE {ref_column} = ?
        """, id)
        rows = cursor.fetchall()
        for row in rows:
            ref_id = row[0]
            # Recursively delete referencing rows
            script_delete_with_related(
                ref_table, ref_id, conn, schema=ref_schema,
                visited=visited, script_list=script_list
            )

    # Delete the main row
    delete_sql = f"DELETE FROM [{schema}].[{table_name}] WHERE [{identity_col}] = {id};"
    script_list.append(delete_sql)
    return script_list

def main():
    parser = argparse.ArgumentParser(description='Generate SQL scripts for inserting or deleting rows with related data.')
    parser.add_argument('action', choices=['insert', 'delete'], help='Action to perform: insert or delete')
    parser.add_argument('table_name', help='Name of the table to operate on')   
    parser.add_argument('id', help='ID of the row to operate on')
    parser.add_argument('--schema', default='dbo', help='Schema of the table (default: dbo)')
    args = parser.parse_args()
    action = args.action
    table_name = args.table_name
    id = args.id
    schema = args.schema
    id = sys.argv[3]
    conn = get_sql_connection()
    if action == 'delete':
        lines = script_delete_with_related(table_name, id, conn, schema=schema)
    else:
        lines = script_insert_with_related(table_name, id, conn, schema=schema)
    print('\n\n'.join(lines))

if __name__ == "__main__":
    main()