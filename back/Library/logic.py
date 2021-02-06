import hashlib

from Library.constants import Schema, Component, Key
from Library.Utilities.core import Formatting
from Library.data import UsersDAO, AuthenticationDAO, SessionsDAO, \
    UserAddedItemsDAO, DetailsDAO, Mapping
from Library.html import HTMLModals
from Library.Utilities.database import Database


class Authenticator:

    def __init__(self, database_file_path):
        self.user_dao = UsersDAO(database_file_path)
        self.authentication_dao = AuthenticationDAO(database_file_path)
        self.sessions_dao = SessionsDAO(database_file_path)

    @staticmethod
    def _hash(string_to_hash):
        return hashlib.md5(string_to_hash.encode()).hexdigest()

    def _password_valid(self, user_id, password):
        expected_password = None
        if user_id:
            # Fetch expected password from database.
            rows = self.authentication_dao.read(None, where_condition={Schema.USER: user_id}, distinct=True)
            if rows:
                password_index = self.authentication_dao.get_column_index(Schema.PASSWORD_HASH)
                expected_password = rows[0][password_index]

        if expected_password:
            if self._hash(password) == expected_password:
                return True
        return False

    def set_password(self, user_id, new_password):
        # Hash password.
        password_hash = self._hash(new_password)

        # Check if user already has a password.
        rows = self.authentication_dao.read(None, where_condition={Schema.USER: user_id}, distinct=True)
        if rows:
            self.authentication_dao.update(
                None,
                {Schema.PASSWORD_HASH: password_hash},
                where_condition={Schema.USER: user_id}
            )
        else:
            self.authentication_dao.new({Schema.USER: user_id, Schema.PASSWORD_HASH: password_hash})

    def start_session(self, user_id, password):
        # TODO add "expires" datetime column so can be filtered by active
        # value can also be returned to client to set cookie expiry datetime.

        # Authenticate user using password.
        if self._password_valid(user_id, password):
            # Generate new session,
            session_key = Database.unique_id()
            self.sessions_dao.new({Schema.USER: user_id, Schema.SESSION_KEY: session_key})
            return session_key
        return None

    def validate_session(self, session_key, user_id):
        # Fetch sessions for this user.
        session_rows = self.sessions_dao.read(None, where_condition={Schema.SESSION_KEY: session_key},
                                              sortby=Schema.CREATED)

        # Return False if no sessions have been started.
        if not session_rows:
            return False

        # Return True if latest user_id matches.
        latest_dict = Formatting.map_rows_to_schema(session_rows, self.sessions_dao.SCHEMA)[0]
        if user_id == latest_dict.get(Schema.USER):
            return True
        return False


class Controller:

    def __init__(self, database_file_path):

        self.user_dao = UsersDAO(database_file_path)
        self.details_dao = DetailsDAO(database_file_path)

        self.dao_map = {c: d(database_file_path) for c, d in Mapping.DAOS.items()}

    def get_user_data(self, user_id=None, email=None):
        user_rows = None
        if user_id:
            user_rows = self.user_dao.read(user_id, distinct=True)
        elif email:
            user_rows = self.user_dao.read(None, where_condition={Schema.EMAIL: email}, distinct=True)

        if user_rows:
            user_data = dict(zip(self.user_dao.SCHEMA, user_rows[0]))
            details_row = self.details_dao.read(None, {Schema.USER: user_data.get(Schema.ID)}, distinct=True)
            if details_row:
                details_dict = dict(zip(self.details_dao.SCHEMA, details_row[0]))
                display_name = details_dict.get(Key.H1)
                user_data[Schema.NAME] = Schema.NAME if display_name == '' else display_name
            return user_data

        return None

    def get_full_user_data(self, user_id, date_format=Formatting.DATETIME_JS_FORMAT, replace_none=False):
        # Return dictionary of users data, can be formatted.

        # Fetch user data from Users table, return None immediately if user_id is not found.
        user_dict = self.get_user_data(user_id=user_id)
        if user_dict is None:
            return None

        # Load singleton components.
        for component in [Component.DETAILS, Component.ABOUT]:
            dao = self.dao_map.get(component)
            rows = dao.read(None, where_condition={Schema.USER: user_id}, distinct=True)
            data = Formatting.map_rows_to_schema(rows, dao.SCHEMA)
            user_dict[component] = data[0] if data else None

        # Load components with multiple entries.
        for component in [Component.EXPERIENCE, Component.QUALIFICATION]:
            dao = self.dao_map.get(component)
            data = dao.read(None, where_condition={Schema.USER: user_id}, sortby=Schema.END)
            dicts = Formatting.map_rows_to_schema(data, dao.SCHEMA)
            formatted_dict = Formatting.format_datetime_strings_in_dict(
                dicts,
                keys=dao.date_time_columns,
                input_format=Formatting.DATETIME_DB_FORMAT,
                output_format=date_format,
                replace_none=replace_none
            )
            user_dict[component] = formatted_dict if formatted_dict else None

        return user_dict

    def new_user(self, email, display_name, headline):
        # Check email has not already been used.
        user_rows = self.user_dao.read(None, where_condition={Schema.EMAIL: email})
        if user_rows:
            return None
        else:
            user_id = self.user_dao.new({Schema.EMAIL: email})
            # Details get added when a new user is created.
            self.details_dao.new({Schema.USER: user_id, Key.H1: display_name, Key.H2: headline})
            return user_id

    def edit(self, validated_user_id, edit_dict, row_id):
        # {'experience': [{column: value}]}
        for section_name, changes in edit_dict.items():
            dao = self.dao_map.get(section_name)
            if dao is not None:
                formatted_changes = Formatting.format_datetime_strings_in_dict(
                    changes,
                    keys=dao.date_time_columns,
                    input_format=Formatting.DATETIME_JS_FORMAT,
                    output_format=Formatting.DATETIME_DB_FORMAT)
                formatted_changes = Formatting.remove_nones_from_dict(formatted_changes)

                # Only allow changes to rows owned by validated_user_id.
                if row_id == validated_user_id:
                    where_condition = {Schema.ID: validated_user_id}
                else:
                    where_condition = {Schema.ID: row_id, Schema.USER: validated_user_id}

                dao.update(None, formatted_changes, where_condition=where_condition)

    def add(self, validated_user_id, add_dict):
        for component, change in add_dict.items():
            dao = self.dao_map.get(component)
            if dao is not None:
                # Add validated user ID as user_id
                change[Schema.USER] = validated_user_id
                formatted_changes = Formatting.format_datetime_strings_in_dict(
                    change,
                    keys=dao.date_time_columns,
                    input_format=Formatting.DATETIME_JS_FORMAT,
                    output_format=Formatting.DATETIME_DB_FORMAT
                )
                dao.new(formatted_changes)

    def delete(self, delete_type, row_id):
        dao = self.dao_map.get(delete_type)
        if dao is not None:
            dao.delete({Schema.ID: row_id})

    # TODO SOMEWHERE ELSE
    def generate_edit_modal(self, edit_type, row_id, user_id):
        user_data = self.get_full_user_data(user_id=user_id)
        html_modals = HTMLModals('/Users/joshnicholls/Desktop/myCV/mapping.json')
        return html_modals.edit_modal(edit_type, row_id, user_data)

    def generate_manage_modal(self, user_id):
        user_data = self.get_full_user_data(user_id=user_id)
        html_modals = HTMLModals('/Users/joshnicholls/Desktop/myCV/mapping.json')
        return html_modals.manage_modal(user_data)


class UserAddedItems:

    def __init__(self, database_file_path):
        self.dao = UserAddedItemsDAO(database_file_path)

    def add_new(self, uai_type, uai_display_name):
        self.dao.new({Schema.DISPLAY_NAME: uai_display_name, Schema.TYPE: uai_type, Schema.COUNT: 0,
                      Schema.VERIFIED: 'true'})

    def get_all(self, uai_type, verified=True):
        if verified:
            condition = {Schema.TYPE: uai_type, Schema.VERIFIED: 'true'}
        else:
            condition = {Schema.TYPE: uai_type}
        return self.dao.read(where_condition=condition)
