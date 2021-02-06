import datetime
import json

from Library.constants import Schema, Components
from Library.core import Database, Formatting


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
        return datetime.datetime.now().strftime(Formatting.DATETIME_DB_FORMAT)

    def create_table(self, table=None, schema=None, foreign_key=None, parent_table=None):
        table = table if table else self.TABLE
        schema = schema if schema else self.SCHEMA
        if table is not None and schema is not None:
            self._database.create_table(table, schema, foreign_key=foreign_key, foreign_table=parent_table)

    def get_column_index(self, column_name):
        if column_name in self.SCHEMA:
            return self.SCHEMA.index(column_name)
        return None

    # Return all values as strings, including date times.
    def read(self, entry_id, where_condition=None, sortby=None, distinct=False):
        if where_condition is not None:
            condition = where_condition
        else:
            condition = {Schema.ID: entry_id} if entry_id is not None else None
        return self._database.select(self.TABLE, condition=condition, distinct=distinct, sortby=sortby)

    # Assume all values are strings, including datetimes.
    def update(self, entry_id, values_dict, where_condition=None):
        if where_condition is not None:
            condition = where_condition
        else:
            condition = {Schema.ID: entry_id} if entry_id is not None else None
        return self._database.update(self.TABLE, values_dict, condition)

    # Assume all values are strings, including date times.
    def new(self, data_dict):
        # Add unique id.
        data_dict[Schema.ID] = Database.unique_id()

        # Check all columns are present.
        missing_columns = [column for column in self.SCHEMA if column not in data_dict.keys()]
        for column in missing_columns:
            data_dict[column] = None

        # Write to row, then return id.
        self._database.insert(self.TABLE, data_dict)
        return data_dict.get(Schema.ID)

    def delete(self, where_condition):
        return self._database.delete(self.TABLE, where_condition)


class UsersDAO(DAO):
    TABLE = 'Users'
    SCHEMA = [Schema.ID, Schema.EMAIL, Schema.HIDDEN]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)


class AuthenticationDAO(DAO):
    TABLE = 'Authentication'
    SCHEMA = [Schema.ID, Schema.USER, Schema.LAST_CHANGED, Schema.PASSWORD_HASH]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)
        self.date_time_columns = [Schema.LAST_CHANGED]

    def new(self, data_dict):
        data_dict[Schema.LAST_CHANGED] = Formatting.datetime_to_string(datetime.datetime.now())
        return super().new(data_dict)


class SessionsDAO(DAO):
    TABLE = 'Sessions'
    SCHEMA = [Schema.ID, Schema.USER, Schema.CREATED, Schema.SESSION_KEY]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)
        self.date_time_columns = [Schema.CREATED]

    def new(self, data_dict):
        data_dict[Schema.CREATED] = Formatting.datetime_to_string(datetime.datetime.now())
        return super().new(data_dict)


class DetailsDAO(DAO):
    TABLE = 'Details'
    SCHEMA = [Schema.ID, Schema.USER, Schema.DISPLAY_NAME, Schema.HEADLINE]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)


class AboutDAO(DAO):
    TABLE = 'About'
    SCHEMA = [Schema.ID, Schema.USER, Schema.TEXT]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)


class ExperiencesDAO(DAO):
    TABLE = 'Experiences'
    SCHEMA = [Schema.ID, Schema.USER, Schema.EMPLOYER, Schema.ROLE, Schema.START, Schema.END, Schema.TEXT]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)
        self.date_time_columns = [Schema.START, Schema.END]


class QualificationsDAO(DAO):
    TABLE = 'Qualifications'
    SCHEMA = [Schema.ID, Schema.USER, Schema.SCHOOL, Schema.SUBJECT, Schema.START, Schema.END, Schema.TEXT]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)
        self.date_time_columns = [Schema.START, Schema.END]


class UserAddedItemsDAO(DAO):
    TABLE = 'UserAddedItems'
    SCHEMA = [Schema.ID, Schema.TYPE, Schema.DISPLAY_NAME, Schema.COUNT, Schema.VERIFIED]

    def __init__(self, database_file_path):
        super().__init__(database_file_path)


class Mapping:
    # JSON file map keys.
    _DISPLAY_TEXT_MAP = 'display_text_map'

    # Component Column Keys.
    TITLE = 'title'
    H1 = 'header_1'
    H2 = 'header_2'
    START = 'start_date'
    END = 'end_date'
    TEXT = 'text'

    # Keys in display order.
    KEYS = [H1, H2, START, END, TEXT]

    DAOS = {
        Components.DETAILS: DetailsDAO,
        Components.ABOUT: AboutDAO,
        Components.EXPERIENCE: ExperiencesDAO,
        Components.QUALIFICATION: QualificationsDAO
    }

    SCHEMA = {
        Components.DETAILS: {
            H1: Schema.DISPLAY_NAME,
            H2: Schema.HEADLINE,
        },
        Components.ABOUT: {
            TEXT: Schema.TEXT,
        },
        Components.EXPERIENCE: {
            H1: Schema.EMPLOYER,
            H2: Schema.ROLE,
            START: Schema.START,
            END: Schema.END,
            TEXT: Schema.TEXT
        },
        Components.QUALIFICATION: {
            H1: Schema.SCHOOL,
            H2: Schema.SUBJECT,
            START: Schema.START,
            END: Schema.END,
            TEXT: Schema.TEXT
        }
    }

    def __init__(self, mapping_file_path):
        self._map = {}
        with open(mapping_file_path) as json_file:
            self._map  = json.load(json_file)

    def get_display_text(self, component, key, default_text=True):
        display_text = '{}_{}'.format(str(component), str(key)) if default_text else None
        component_map = self._map.get(self._DISPLAY_TEXT_MAP).get(component)
        if component_map:
            display_text = component_map.get(key, display_text)
        return display_text

    def get_database_name(self, component, key):
        component_map = self.SCHEMA.get(self._DISPLAY_TEXT_MAP).get(component)
        if component_map:
            return component_map.get(key)
        return None





