"""
Honkbot database models

This module is used to interact with a PostgreSQL database. It assumes the database is to look like this:

DB: honkbot
  Table: ddr_codes
    user_id: PRIMARY VARCHAR(100)
    name: VARCHAR(8) NOT NULL (ie. MEATBEAN)
    code: VARCHAR(9) NOT NULL (ie. 1234-5678)
    rank: VARCHAR(5) (ie. 10dan, 2kyu, chuu, kai)
  Table: iidx_codes
    user_id: PRIMARY VARCHAR(100)
    name: VARCHAR(6) NOT NULL (ie. SPOOKY)
    code: VARCHAR(9) NOT NULL (ie. 1234-5678)
    rank: VARCHAR(5) (ie. 10dan, 2kyu, chuu, kai)

"""

import os

import dotenv
import psycopg2


class CodeDatabaseModel:
    """
    Base model inherited to interact with the different tables in the database

    Args:
        table (str): Name of the database table to interact with

    """
    def __init__(self, table=None):

        self.AVAILABLE_ATTRIBUTES = [
            "name",
            "code",
            "rank"
        ]

        dotenv.load_dotenv()
        password = os.getenv("POSTGRES_PASSWORD")
        user = os.getenv("POSTGRES_USER")
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        self.name = ""
        self.code = ""
        self.rank = ""
        self.table = table
        self._conn = psycopg2.connect(
            dbname="honkbot",
            user=user,
            password=password,
            host=host,
            port=port
        )
        self._cursor = self._conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):

        self._cursor.close()
        self._conn.close()
        return bool(exc_type is None)

    def _create_entry(self, table, user_id, **kwargs):

        name = kwargs.get("name")
        code = kwargs.get("code")
        rank = kwargs.get("rank")

        if not name or not code:
            raise Exception("Name and code are required attributes")
        self._cursor.execute(
            "INSERT INTO %s (user_id, name, code, rank) VALUES (%s, %s, %s, %s);",
            (table, user_id, name, code, rank)
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
    """
    Object representing a DDR Dancer

    Args:
        user_id (str): Discord User ID to reference
    """
    def __init__(self, user_id=None):
        self.user_id = user_id
        super().__init__("ddr_codes")

    def create(self, name=None, code=None, rank=None):
        """
        Creates a DDR Dancer in the database

        Args:
            name (str): 8 character dancer name submitted to eAmuse
            code (str): 9 character dancer ID (####-####)

        Optional:
            rank (str): Dan ranking of user

        Returns:
            None
        """
        if not name:
            raise Exception("An 8 character dancer name is required when creating a new entry")
        if not code:
            raise Exception("A DDR code (####-####) is required when creating a new entry")

        self._create_entry(self.table, self.user_id, name=name, code=code, rank=rank)

    def update(self, **kwargs):
        """
        Updates a DDR dancer in the database

        Args:
            **kwargs: The data to be updated

        Options:
            name (str): 8 character dancer name submitted to eAmuse
            code (str): 9 character dancer ID (####-####)
            rank (str): Dan ranking of user

        Returns:
            None
        """

        # If there's nothing to update...well there's nothing to update
        if not kwargs.items():
            return
        for key, _ in kwargs.items():
            # If something is inputted that shouldn't be, raise
            if key not in self.AVAILABLE_ATTRIBUTES:
                raise Exception(f'"{key}" is not a valid attribute to update')

        self._update_entry(self.table, self.user_id, **kwargs)

    def delete(self):
        """
        Deletes a DDR dancer from the database

        Args:
            None

        Returns:
            None
        """

        self._delete_entry(self.table, self.user_id)


class IIDXCode(CodeDatabaseModel):
    """
    Object representing a IIDX player

    Args:
        user_id (str): Discord User ID to reference
    """
    def __init__(self, user_id=None):
        self.user_id = user_id
        table = "iidx_codes"
        super().__init__(table)

    def create(self, name=None, iidx_id=None, rank=None):
        """
        Creates a IIDX player in the database

        Args:
            name (str): DJ Name of the player
            iidx_id (str): ID of the IIDX player
        Optional:
            rank (str): Dan ranking of the player

        Returns:
            None
        """
        if not name or len(name) > 6:
            raise Exception("A 6 character DJ name is required when creating a new entry")
        if not iidx_id:
            raise Exception("A IIDX ID is required when creating a new entry")

        self._create_entry(self.table, self.user_id, name=name, code=iidx_id, rank=rank)

    def update(self, **kwargs):
        """
        Updates a IIDX player in the database

        Args:
            kwargs (dict): Data to be updated
        Options:
            name (str): DJ name of the player
            code (str): IIDX ID of the player
            rank (str): Dan ranking of the player

        Returns:
            None
        """

        # If there's nothing to update...well there's nothing to update
        if not kwargs.items():
            return
        for key, _ in kwargs.items():
            # If something is inputted that shouldn't be, raise
            if key not in self.AVAILABLE_ATTRIBUTES:
                raise Exception(f'"{key}" is not a valid attribute to update')

        self._update_entry(self.table, self.user_id, **kwargs)

    def delete(self):
        """
        Deletes a player from the database

        Args:
            None

        Returns:
            None
        """

        self._delete_entry(self.table, self.user_id)
