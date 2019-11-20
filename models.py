import psycopg2


class DatabaseModel:
    def __init__(self, table=None):
        self.table = table
        self.conn = psycopg2.connect(
            dbname="honkbot",
            user="honkbot",
            password=password,
            host=host
        )
        self.cursor = self.conn.cursor()

class DDRCode(DatabaseModel):
    def __init__(self, user_id=None):
        self.user_id = user_id
        table = "ddr_codes"
        super().__init__(table)

    def create(self, name=None, ddr_code=None):
        pass
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
