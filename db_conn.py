class Cursor:

    def execute(sql: str, args: tuple=None):
        pass

    def fetchone(sql: str, args: tuple=None) -> list:
        pass

    def fetchall(sql: str, args: tuple=None) -> list[list]:
        pass

class DbConn:
    
    def cursor() -> Cursor:
        pass