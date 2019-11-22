import os

import dotenv
import psycopg2


class CodeDatabaseModel:
    def __init__(self, table=None):
        
        dotenv.load_dotenv()
        password = os.getenv("POSTGRES_PASSWORD")
        user = os.getenv("POSTGRES_USER")
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        self.name = ""
        self.code = ""
        self.table = table
        self._conn = psycopg2.connect(
            dbname="honkbot",
            user=user,
            password=password,
            host=f"{host}:{port}"
        )
        self._cursor = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):

        self._cursor.close()
        self._conn.close()
        return True if exc_type is None else False

    def _create_entry(self, table, user_id, name, code):

        self._cursor.execute(
            "INSERT INTO %s (user_id, name, code) VALUES (%s, %s, %s);",
            (table, user_id, name, code)
        )
        self._conn.commit()

    def _get_entry(self, table, user_id):

        self._cursor.execute(
            'SELECT * from %s WHERE user_id="%s";',
            (table, user_id)
        )
        return self._cursor.fetchone()

    def _list_entries(self, table):

        self._cursor.execute("SELECT * FROM %s", (table,))
        return self._cursor.fetchall()

    def _update_entry(self, table, user_id, **kwargs):

        entry = self._get_entry(table, user_id)
        if not entry:
            raise Exception(f"Entry for user_id {user_id} not found. Entry must be created first")

        set_values = ", ".join([f"{item[0]}={item[1]}" for item in list(kwargs.items())])
        self._cursor.execute(
            'UPDATE %s SET %s WHERE user_id="%s";',
            (table, set_values, user_id)
        )
        self._conn.commit()

    def _delete_entry(self, table, user_id):

        entry = self._get_entry(table, user_id)
        if not entry:
            raise Exception(f"Entry for user_id {user_id} not found. Entry must be created first")

        self._cursor.execute(
            'DELETE FROM %s WHERE user_id="%s";',
            (table, user_id)
        )
        self._conn.commit()

class DDRCode(CodeDatabaseModel):
    def __init__(self, user_id=None):
        self.user_id = user_id
        table = "ddr_codes"
        super().__init__(table)

    def create(self, name=None, code=None):
        if not name:
            raise Exception("An 8 character dancer name is required when creating a new entry")
        if not code:
            raise Exception("A DDR code (####-####) is required when creating a new entry")

        self._create_entry(self.table, self.user_id, name, code)

    def update(self, user_id, **kwargs):
        pass
    def delete(self):
        pass

class IIDXCode(CodeDatabaseModel):
    def __init__(self, user_id=None):
        self.user_id = user_id
        table = "iidx_codes"
        super().__init__(table)

    def create(self, name=None, iidx_id=None):
        pass
    def update(self, **kwargs):
        pass
    def delete(self):
        pass
