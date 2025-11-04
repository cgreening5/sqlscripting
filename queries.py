class Queryer:
    def __init__(self, conn):
        self.conn = conn

    def views(self, text=None):        
        cursor = self.conn.cursor()
        if text:
            cursor.execute(f"""
                select name, OBJECT_DEFINITION(object_id) from sys.views where OBJECT_DEFINITION(object_id) like '%{text}%'
            """)
        else:
            cursor.execute(f"""
                select name, OBJECT_DEFINITION(object_id) from sys.views
            """)
        results = cursor.fetchall()
        return results
    
    def procedures(self, text=None):        
        cursor = self.conn.cursor()
        if text:
            cursor.execute(f"""
                select name, OBJECT_DEFINITION(object_id) from sys.procedures where OBJECT_DEFINITION(object_id) like '%{text}%'
            """)
        else:
            cursor.execute(f"""
                select name, OBJECT_DEFINITION(object_id) from sys.procedures
            """)
        results = cursor.fetchall()
        return results

    def triggers(self, text=None):        
        cursor = self.conn.cursor()
        if text:
            cursor.execute(f"""
                select name, OBJECT_DEFINITION(object_id) from sys.triggers where OBJECT_DEFINITION(object_id) like '%{text}%'
            """)
        else:
            cursor.execute(f"""
                select name, OBJECT_DEFINITION(object_id) from sys.triggers
            """)
        results = cursor.fetchall()
        return results