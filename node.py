from dataservice import DataService

class Node:

    def __init__(self, name, identity_col, id, schema='dbo'):
        self.id = id
        self.schema = schema
        self.name = name
        self.identity_col = identity_col
        self.columns = []
        self.vals = {}
        self.references = {}
        self.back_references = []

    def reference(self, column, node, primary_key):
        if column not in self.references:
            self.references[column] = (node, primary_key)
            node.back_references.append((self, column))

class Builder:

    def __init__(self, dataservice: DataService, foreign_keys):
        self.dataservice = dataservice
        self.visited = {}
        self.foreign_keys = foreign_keys

    def build_node(self, schema, table_name, id):
        node = self._build_node(schema, table_name, id)
        self._build_references(node)
        return node

    def _build_node(self, schema, table_name, id):
        if (schema, table_name, id) in self.visited:
            return self.visited[(schema, table_name, id)]
        node = Node(table_name, self.dataservice.get_identity(table_name, schema), id, schema)
        node.columns = self.dataservice.get_columns(node.schema, node.name)
        self._get_values(node)
        if not node:
            raise ValueError(f"Table {table_name} not found in schema {schema}")
        return node
    
    def _get_values(self, node: Node):
        values = self.dataservice.get_values(node.name, node.identity_col, node.id, node.columns, node.schema)
        for column, value in zip(node.columns, values):
            node.vals[column] = value

    def _build_references(self, node: Node):
        for pk_schema, pk_table, pk_column, fk_column, fk_name in self.dataservice.get_references(node.schema, node.name):
            if fk_name not in self.foreign_keys:
                continue
            if node.vals.get(fk_column) is None:
                continue
            ref_table = self._build_node(pk_schema, pk_table, node.vals[fk_column])
            node.reference(fk_column, ref_table, pk_column)
        for pk_column, fk_schema, fk_table, fk_column, fk_name in self.dataservice.get_back_references(node.name):
            for id in self.dataservice.get_referencing_rows(fk_schema, fk_table, fk_name, node.id):
                ref_table = self.build_node(fk_schema, fk_table, id)
                ref_table.reference(fk_column, node, node.identity_col)
            