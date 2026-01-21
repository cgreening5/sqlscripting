  
from scripting.node import Node


class DeleteScripter:

    def __init__(self, node: Node, print_summary=True, transaction=False):
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
        if self.transaction:
            self.lines.append("COMMIT TRANSACTION;\n")
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
