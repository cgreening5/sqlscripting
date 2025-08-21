from node import Node


class InsertScripter:

    def __init__(self, node: Node, print_summary=True):
        self.node = node
        self.lines = []
        self.summary = {}
        self.visited = set()
        self.print_summary = print_summary

    def script(self):
        self._script(self.node)
        if self.print_summary:
            print("-- Summary of changes:")
            for table, count in self.summary.items():
                print(f"-- - {count} inserts to {table}")
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
    
class DeleteScripter:

    def __init__(self, node: Node, print_summary=True):
        self.node = node
        self.lines = []
        self.summary = {}
        self.visited = set()
        self.print_summary = print_summary

    def script(self):
        self._script(self.node)
        return self.lines

    def _script(self, node):
        if self._to_variable(node) in self.visited:
            return
        self.visited.add(self._to_variable(node))
        for table, _ in node.back_references:
            self._script(table)
        self._script_table(node)
        for table, _ in node.references.values():
            self._script(table)

    def _script_table(self, node: Node):
        self.lines.append(
            f"DELETE FROM [{node.schema}].[{node.name}] WHERE [{node.identity_col}] = {node.id};")

    def _to_variable(self, node):
        return f"@{node.schema}_{node.name}_{node.id}"
