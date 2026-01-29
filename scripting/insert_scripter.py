from scripting.node import Node


class InsertScripter:

    def __init__(self, node: Node, print_summary=False, transaction=False):
        self.node = node
        self.lines = []
        self.summary = {}
        self.visited = set()
        self.print_summary = print_summary
        self.transaction = transaction

    def script(self):
        if self.transaction:
            self.lines.append("BEGIN TRANSACTION;\n")
            self.lines.append("SET XACT_ABORT ON;\n")
        self._script(self.node)
        if self.print_summary:
            print("-- Summary of changes:")
            for table, count in self.summary.items():
                print(f"-- - {count} inserts to {table}")
        if self.transaction:
            self.lines.append("COMMIT TRANSACTION;\n")
        return self.lines

    def _script(self, node):
        if (node.schema, node.name, node.id) in self.visited:
            return
        self.visited.add((node.schema, node.name, node.id))
        for table, _ in node.references.values():
            self._script(table)
        self._script_table(node)
        for table, _ in node.back_references:
            self._script(table)

    def _script_table(self, node: Node):
        values = []
        for col in node.columns:
            val = node.vals[col]
            if val == None:
                values.append('NULL')
            elif col in node.references:
                ref: Node = node.references[col][0]
                values.append(self._get_variable(ref))
            elif isinstance(val, str):
                values.append(f"'{val.replace('\'', '\'\'')}'")
            elif isinstance(val, bool):
                values.append('1' if val else '0')
            else:
                values.append(str(val))
        self.lines.append(
            f"INSERT INTO [{node.schema}].[{node.name}] (\n\t[{'],\n\t['.join(node.columns)}]\n)\n" + \
            f"VALUES (\n\t{',\n\t'.join(values)}\n);")
        if len(node.back_references) > 0:
            self.lines.append(f"DECLARE {self._get_variable(node)} INT = SCOPE_IDENTITY()")
        self.lines[-1] += "\n"
        self.summary[node.name] = self.summary.get(node.name, 0) + 1

    def _get_variable(self, node: Node):
        return f"@{node.schema}_{node.name}_{node.id}"