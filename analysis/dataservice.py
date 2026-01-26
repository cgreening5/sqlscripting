from db_conn import DbConn


class DataService:

    def __init__(self, conn: DbConn):
        self.conn = conn

    def _fetch_one(self, sql, args):
        with self.conn.cursor() as cursor:
            cursor.execute(sql, args)
            return cursor.fetchone()


    def get_object_type(self, name: str) -> str:
        sql = 'SELECT TYPE FROM sys.objects where sys.objects.name = ?'
        return self._fetch_one(sql, name)

    def get_view_definition(self, name: str) -> str:
        sql = "select view_definition from INFORMATION_SCHEMA.VIEWS where TABLE_NAME = ?"
        return self._fetch_one(sql, name)