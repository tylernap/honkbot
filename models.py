import os

import dotenv
import psycopg2


class DatabaseModel:
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

    def __exit__(self, exc_type, exc_value, traceback):

        self._cursor.close()
        self._conn.close()

    def __del__(self):

        self._cursor.close()
        self._conn.close()

    def _create_entry(self, table, user_id, name, code):

        self._cursor.execute(
            f"INSERT INTO {table} (user_id, name, code) VALUES (%s, %s, %s);",
            (user_id, name, code)
        )
        self._conn.commit()

class DDRCode(DatabaseModel):
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

    def update(self, **kwargs):
        pass
    def delete(self):
        pass

class IIDXCode(DatabaseModel):
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
