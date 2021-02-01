import json
import os

from Library.core import Database, Constants, Formatting
from Library.constants import SCHEMA
import datetime

import sqlite3


class DAO:
    TABLE = None
    SCHEMA = None

    def __init__(self, database_file_path, volatile=False):
        self._database = Database(database_file_path)
        self.date_time_columns = None
        self.volatile = volatile
        self.database_file_path = database_file_path

    @staticmethod
    def _current_time_as_string():
        return datetime.datetime.now().strftime(Constants.DATETIME_DB_FORMAT)

    def create_table(self, table=None, schema=None, foreign_key=None, parent_table=None):
        table = table if table else self.TABLE
        schema = schema if schema else self.SCHEMA
        if table is not None and schema is not None:
            self._database.create_table(table, schema, foreign_key=foreign_key, foreign_table=parent_table)

    def get_column_index(self, column_name):
        if column_name in self.SCHEMA:
            return self.SCHEMA.index(column_name)
        return None

    # Return all values as strings, including datetimes.
    def read(self, entry_id, where_condition=None, sortby=None, distinct=False):
        if where_condition is not None:
            condition = where_condition
        else:
            condition = {SCHEMA.ID: entry_id} if entry_id is not None else None
        return self._database.select(self.TABLE, condition=condition, distinct=distinct, sortby=sortby)

    # Assume all values are strings, including datetimes.
    def update(self, entry_id, values_dict, where_condition=None):
        if where_condition is not None:
            condition = where_condition
        else:
            condition = {SCHEMA.ID: entry_id} if entry_id is not None else None
        return self._database.update(self.TABLE, values_dict, condition)

    # Assume all values are strings, including datetimes.
    def new(self, data_dict):
        # Add unique id.
        data_dict[SCHEMA.ID] = Database.unique_id()

        # Check all columns are present.
        missing_columns = [column for column in self.SCHEMA if column not in data_dict.keys()]
        for column in missing_columns:
            data_dict[column] = None

        # Write to row, then return id.
        self._database.insert(self.TABLE, data_dict)
        return data_dict.get(SCHEMA.ID)

    def delete(self, where_condition):
        return self._database.delete(self.TABLE, where_condition)


class UsersDAO(DAO):
    TABLE = 'Users'
    SCHEMA = [SCHEMA.ID, SCHEMA.USER_EMAIL, SCHEMA.USER_DISPLAY_NAME, SCHEMA.USER_TITLE, SCHEMA.USER_HIDDEN]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)

    def read_like_display_name(self, search_string):
        pass


class UserAddedItemsDAO(DAO):
    TABLE = 'UserAddedItems'
    SCHEMA = [SCHEMA.ID, 'type', 'display_name', 'count', 'verified']

    def __init__(self, database_file_path):
        super().__init__(database_file_path)


class AuthenticationDAO(DAO):
    TABLE = 'Authentication'
    SCHEMA = [SCHEMA.ID, SCHEMA.LAST_CHANGED, SCHEMA.USER_ID, SCHEMA.PASSWORD_HASH]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)
        self.date_time_columns = [SCHEMA.LAST_CHANGED]

    def new(self, data_dict):
        data_dict[SCHEMA.LAST_CHANGED] = Formatting.datetime_to_string(datetime.datetime.now())
        return super().new(data_dict)


class SessionsDAO(DAO):
    TABLE = 'Sessions'
    SCHEMA = [SCHEMA.ID, SCHEMA.USER_ID, SCHEMA.DATE_CREATED, SCHEMA.SESSION_KEY]

    def __init__(self, database_file_path):
        self.date_time_columns = [SCHEMA.DATE_CREATED]
        super().__init__(database_file_path)

    def new(self, data_dict):
        data_dict[SCHEMA.DATE_CREATED] = Formatting.datetime_to_string(datetime.datetime.now())
        return super().new(data_dict)


class BiosDAO(DAO):
    TABLE = 'Bios'
    SCHEMA = [SCHEMA.ID, SCHEMA.USER_ID, SCHEMA.CONTENT]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)


class ExperiencesDAO(DAO):
    TABLE = 'Experiences'
    SCHEMA = [SCHEMA.ID, SCHEMA.USER_ID, SCHEMA.START_DATE, SCHEMA.END_DATE, SCHEMA.EXP_EMPLOYER, SCHEMA.EXP_ROLE, SCHEMA.CONTENT]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)
        self.date_time_columns = [SCHEMA.START_DATE, SCHEMA.END_DATE]


class QualificationsDAO(DAO):
    TABLE = 'Qualifications'
    SCHEMA = [SCHEMA.ID, SCHEMA.USER_ID, SCHEMA.START_DATE, SCHEMA.END_DATE, SCHEMA.QUAL_SCHOOL, SCHEMA.QUAL_SUBJECT, SCHEMA.CONTENT]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)
        self.date_time_columns = [SCHEMA.START_DATE, SCHEMA.END_DATE]


class EmployersDAO(DAO):
    TABLE = 'Employers'
    SCHEMA = [SCHEMA.ID]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)


class SchoolsDAO(DAO):
    TABLE = 'Schools'
    SCHEMA = [SCHEMA.ID]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)


class DatabaseInitiator:
    DAOS_TO_INITIATE = [UsersDAO, BiosDAO, ExperiencesDAO, QualificationsDAO, AuthenticationDAO, SessionsDAO]

    @staticmethod
    def create_tables(database_file_path, foreign_key=None, parent_table=None):
        # foreign_key = 'user_id', parent_table = 'Users'
        # Open new database file.
        if not os.path.isfile(database_file_path):
            with open(database_file_path, 'w+'):
                pass
            print('Created database file "{}".'.format(database_file_path))

        # Create tables.
        for dao in DatabaseInitiator.DAOS_TO_INITIATE:
            try:
                if dao.TABLE == parent_table:
                    dao(database_file_path).create_table()
                else:
                    dao(database_file_path).create_table(foreign_key=foreign_key, parent_table=parent_table)
                # if dao.TABLE == parent_table:
                #     print('Created parent table table "{}" in "{}".'.format(dao.TABLE, database_file_path))
                # else:
                #
                # if foreign_key is not None and parent_table is not None:
                #     print('Created cascading table "{}" in "{}".'.format(dao.TABLE, database_file_path))
                # else:
                #     print('Created table "{}" in "{}".'.format(dao.TABLE, database_file_path))

            except sqlite3.OperationalError as e:
                print('WARNING: Could not create table "{}". SQL Error: "{}"'.format(dao.TABLE, e))

    @staticmethod
    def copy_data(source_file_path, destination_file_path, force_all=False):
        if force_all:
            daos_to_copy = DatabaseInitiator.DAOS_TO_INITIATE
        else:
            daos_to_copy = [dao for dao in DatabaseInitiator.DAOS_TO_INITIATE if not dao(source_file_path).volatile]

        table_rows = {}
        source_database = Database(source_file_path)
        for dao in daos_to_copy:
            try:
                table_rows[dao.TABLE] = dao(source_file_path).read()[1:]
                print('Copied "{}" data to "{}".'.format(dao.TABLE, destination_file_path))
            except sqlite3.OperationalError as e:
                print('WARNING: Could not copy "{}" data. SQL Error: "{}"'.format(dao.TABLE, e))

        destination_database = Database(destination_file_path)
        for table in table_rows:
            rows = [list(r) for r in table_rows.get(table)]
            destination_database.insert_multiple(table, rows)



