from dataservice import DataService

class Node:

    def __init__(self, name, identity_col, id, schema='dbo'):
        self.id = id
        self.schema = schema
        self.name = name
        self.identity_col = identity_col
        self.columns = []
        self.foreign_keys = []
        self.vals = {}
        self.references = {}
        self.back_references = []

    def reference(self, column, node, primary_key):
        if column not in self.references:
            self.references[column] = (node, primary_key)
            node.back_references.append((self, column))

    def __repr__(self):
        return f"Node({self.schema}.{self.name}, {self.id})"

class Builder:

    def __init__(self, dataservice: DataService, reference_tables: list[str]=None):
        self.dataservice = dataservice
        self.visited = {}
        self.reference_tables = reference_tables or []

    def build_node(self, schema, table_name, id):
        node = self._build_node(schema, table_name, id)
        self._build_references(node)
        self._build_back_references(node)
        self.finalize_references(node)
        return node

    def _build_node(self, schema, table_name, id):
        node = Node(table_name, self.dataservice.get_identity(table_name, schema), id, schema)
        self.visited[(schema, table_name, id)] = node
        node.columns = self.dataservice.get_columns(node.schema, node.name)
        node.foreign_keys = self.dataservice.get_references(node.schema, node.name)
        self._get_values(node)
        if not node:
            raise ValueError(f"Table {table_name} not found in schema {schema}")
        return node
    
    def _get_values(self, node: Node):
        values = self.dataservice.get_values(node.name, node.identity_col, node.id, node.columns, node.schema)
        for column, value in zip(node.columns, values):
            node.vals[column] = value

    def _build_references(self, node: Node):
        for pk_schema, pk_table, pk_column, fk_column, fk_name in node.foreign_keys:
            if pk_table in self.reference_tables:
                continue
            if node.vals.get(fk_column) is None:
                continue
            if (pk_schema, pk_table, node.vals[fk_column]) in self.visited:
                continue
            referenced_node = self._build_node(pk_schema, pk_table, node.vals[fk_column])
            self._build_references(referenced_node)

    def _build_back_references(self, node: Node):
        for _, fk_schema, fk_table, _, fk_name in self.dataservice.get_back_references(node.name):
            for id in self.dataservice.get_referencing_rows(fk_schema, fk_table, fk_name, node.id):
                if (fk_schema, fk_table, id) in self.visited:
                    continue
                print(fk_schema, fk_table, id)
                referencing_node = self._build_node(fk_schema, fk_table, id)
                self._build_references(referencing_node)
                self._build_back_references(referencing_node)
        
    def finalize_references(self, node: Node):
        for node in self.visited.values():
            for pk_schema, pk_table, _, fk_column, _ in node.foreign_keys:
                if (pk_schema, pk_table, node.vals[fk_column]) in self.visited:
                    referenced_node = self.visited[(pk_schema, pk_table, node.vals[fk_column])]
                    node.reference(fk_column, referenced_node, node.vals[fk_column])