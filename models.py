"""
Honkbot database models

This module is used to interact with a PostgreSQL database.

Usage:
    import models
    user = models.DDRCode("MyDiscordID")
    print(user.name) # Returns the stored name of the user
    user.create(name="TEST", code="1234-5678", rank="9dan")
    user.update(code="8888-8888")
    user.update(name="TESTING", rank="10dan")
    user.delete()

It assumes the database is to look like this:

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
        self.name = None
        self.code = None
        self.rank = None
        self.table = table
        self._conn = psycopg2.connect(
            dbname="honkbot",
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT")
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
            f"INSERT INTO {table} (user_id, name, code, rank) VALUES (%s, %s, %s, %s);",
            (user_id, name, code, rank)
        )
        self._conn.commit()

    def _get_entry(self, table, user_id):

        self._cursor.execute(
            f'SELECT * from {table} WHERE user_id=%s;',
            (user_id,)
        )
        entry = self._cursor.fetchone()
        if entry:
            return entry
        else:
            return (user_id, None, None, None)

    def _list_entries(self, table):

        self._cursor.execute(f"SELECT * FROM {table}")
        return self._cursor.fetchall()

    def _search_entries(self, table, **filters):

        search_string = " AND ".join([f"{item[0]} = '{item[1]}'" for item in list(filters.items())])
        self._cursor.execute(f"SELECT * from {table} WHERE {search_string};")
        response = self._cursor.fetchall()

        return response

    def _update_entry(self, table, user_id, **kwargs):

        entry = self._get_entry(table, user_id)
        if not entry:
            raise Exception(f"Entry for user_id {user_id} not found. Entry must be created first")

        set_values = ", ".join([f"{item[0]} = '{item[1]}'" for item in list(kwargs.items())])
        self._cursor.execute(
            f'UPDATE {table} SET {set_values} WHERE user_id=%s;',
            (user_id,)
        )
        self._conn.commit()

    def _delete_entry(self, table, user_id):

        entry = self._get_entry(table, user_id)
        if not entry:
            raise Exception(f"Entry for user_id {user_id} not found. Entry must be created first")

        self._cursor.execute(
            'DELETE FROM {table} WHERE user_id=%s;',
            (user_id,)
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
        _, self.name, self.code, self.rank = self._get_entry(self.table, self.user_id)

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
        if not name or len(name) > 8:
            raise Exception(
                "An dancer name with at most 8 charactersis required when creating a new entry"
            )
        if not code:
            raise Exception("A DDR code (####-####) is required when creating a new entry")

        self._create_entry(self.table, self.user_id, name=name, code=code, rank=rank)
        _, self.name, self.code, self.rank = self._get_entry(self.table, self.user_id)

    def search(self, **filters):
        """
        Searches database for given filters

        Args:
            **filters: Data to filter on

        Options:
            name (str): 8 character dancer name submitted to eAmuse
            code (str): 9 character dancer ID (####-####)
            rank (str): Dan ranking of user

        Returns:
            List: Entries matching given filters
        """

        if not filters.items():
            return []

        # Validate search filters
        for key, _ in filters.items():
            if key not in self.AVAILABLE_ATTRIBUTES:
                raise Exception(f'"{key}" is not a valid attribute to search for')

        return self._search_entries(self.table, **filters)

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
        _, self.name, self.code, self.rank = self._get_entry(self.table, self.user_id)

    def delete(self):
        """
        Deletes a DDR dancer from the database

        Args:
            None

        Returns:
            None
        """

        self._delete_entry(self.table, self.user_id)
        self.name = None
        self.code = None
        self.rank = None

class IIDXCode(CodeDatabaseModel):
    """
    Object representing a IIDX player

    Args:
        user_id (str): Discord User ID to reference
    """
    def __init__(self, user_id=None):
        self.user_id = user_id
        super().__init__("iidx_codes")

        _, self.name, self.code, self.rank = self._get_entry(self.table, self.user_id)

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
            raise Exception(
                "A DJ name with at most 6 characters is required when creating a new entry"
            )
        if not iidx_id:
            raise Exception("A IIDX ID is required when creating a new entry")

        self._create_entry(self.table, self.user_id, name=name, code=iidx_id, rank=rank)
        _, self.name, self.code, self.rank = self._get_entry(self.table, self.user_id)

    def search(self, **filters):
        """
        Searches database for given filters

        Args:
            **filters: Data to filter on

        Options:
            name (str): 6 character dancer name submitted to eAmuse
            code (str): 9 character IIDX ID (####-####)
            rank (str): Dan ranking of user

        Returns:
            List: Entries matching given filters
        """

        if not filters.items():
            return []

        # Validate search filters
        for key, _ in filters.items():
            if key not in self.AVAILABLE_ATTRIBUTES:
                raise Exception(f'"{key}" is not a valid attribute to search for')

        return self._search_entries(self.table, **filters)

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
        _, self.name, self.code, self.rank = self._get_entry(self.table, self.user_id)

    def delete(self):
        """
        Deletes a player from the database

        Args:
            None

        Returns:
            None
        """

        self._delete_entry(self.table, self.user_id)
        self.name = None
        self.code = None
        self.rank = None
