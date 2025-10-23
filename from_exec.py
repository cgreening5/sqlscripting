class FromExecParser:

    def parse(self, sql: str):
        self.sql = sql
        self.pos = 0

    def expect(self, str):
        