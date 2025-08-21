class DataService:

    def __init__(self, conn):
        self.conn = conn

    def get_identity(self, table_name, schema='dbo'):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ? AND COLUMNPROPERTY(object_id('[{schema}].[{table_name}]'), COLUMN_NAME, 'IsIdentity') = 1
        """, table_name)
        cols = cursor.fetchone()
        if cols is None:
            raise Exception("Unable to find identity column for table " + table_name)
        return cols[0]
    
    def get_references(self, schema, table_name):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT pk_schema.name, pk_tab.name, pk_col.name, fk_col.name, fk.name
            FROM sys.foreign_key_columns fkc
                INNER JOIN sys.foreign_keys fk on fk.object_id = fkc.constraint_object_id
                INNER JOIN sys.tables fk_tab ON fk_tab.object_id = fkc.parent_object_id
                INNER JOIN sys.columns fk_col ON fk_col.column_id = fkc.parent_column_id 
                    AND fk_col.object_id = fk_tab.object_id
                INNER JOIN sys.tables pk_tab ON pk_tab.object_id = fkc.referenced_object_id
                INNER JOIN sys.columns pk_col ON pk_col.column_id = fkc.referenced_column_id AND pk_col.object_id = pk_tab.object_id
                INNER JOIN sys.schemas pk_schema ON pk_schema.schema_id = pk_tab.schema_id
            WHERE fk_tab.name = ?""", table_name
        )
        return cursor.fetchall()
        
    def get_back_references(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT pk_col.name AS primary_key_column, fk_schema.name AS referencing_schema, 
            fk_tab.name AS referencing_table, fk_col.name AS referencing_column, fk.name as fk_name
            FROM sys.foreign_key_columns fkc
            INNER JOIN sys.foreign_keys fk ON fk.object_id = fkc.constraint_object_id
            INNER JOIN sys.tables pk_tab ON pk_tab.object_id = fkc.referenced_object_id
            INNER JOIN sys.columns pk_col ON pk_col.column_id = fkc.referenced_column_id AND pk_col.object_id = pk_tab.object_id
            INNER JOIN sys.tables fk_tab ON fk_tab.object_id = fkc.parent_object_id
            INNER JOIN sys.columns fk_col ON fk_col.column_id = fkc.parent_column_id AND fk_col.object_id = fk_tab.object_id
            INNER JOIN sys.schemas fk_schema ON fk_schema.schema_id = fk_tab.schema_id
            WHERE pk_tab.name = ?
        """, table_name)
        return cursor.fetchall()
    
    def get_columns(self, schema, table_name):
        cursor = self.conn.cursor()
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
        return [row[0] for row in cursor.fetchall()]

    def get_values(self, table_name, identity_col, id, columns, schema='dbo'):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT [{'], ['.join(columns)}]
            FROM [{schema}].[{table_name}]
            WHERE [{identity_col}] = ?
        """, (id,))
        values = cursor.fetchone()
        if values is None:
            raise ValueError(f"No values found for {table_name} with {identity_col} = {id}")
        return values
    
    def get_referencing_rows(self, schema, table_name, fk_name, fk_val):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT COL_NAME(fkc.parent_object_id, fkc.parent_column_id), COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id)
            FROM sys.foreign_keys fk
                JOIN sys.foreign_key_columns fkc on fkc.constraint_object_id = fk.object_id
            WHERE fk.name = ?
        """, (fk_name,))
        data = cursor.fetchone()
        if data is None:
            raise ValueError(f"No foreign key columns found for {fk_name}")
        [fk_col, pk_col] = data
        cursor.execute(f"""
            SELECT {pk_col} 
            FROM [{schema}].[{table_name}]
            WHERE [{fk_col}] = ?
        """, (fk_val,))
        return [row[0] for row in cursor.fetchall()]