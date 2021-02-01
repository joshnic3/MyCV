import hashlib

from Library.constants import CvParts, SCHEMA
from Library.core import Database, Formatting
from Library.data import UsersDAO, BiosDAO, ExperiencesDAO, QualificationsDAO, AuthenticationDAO, SessionsDAO, \
    UserAddedItemsDAO
from Library.html import HTMLModals


class Authenticator:

    def __init__(self, database_file_path):
        self._session_key = None
        self.user_id = None

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
            rows = self.authentication_dao.read(None, where_condition={SCHEMA.USER_ID: user_id}, distinct=True)
            if rows:
                password_index = self.authentication_dao.get_column_index(SCHEMA.PASSWORD_HASH)
                expected_password = rows[0][password_index]

        if expected_password:
            if self._hash(password) == expected_password:
                return True
        return False

    def set_password(self, user_id, new_password):
        # Hash password.
        password_hash = self._hash(new_password)

        # Check if user already has a password.
        rows = self.authentication_dao.read(None, where_condition={SCHEMA.USER_ID: user_id}, distinct=True)
        if rows:
            self.authentication_dao.update(
                None,
                {SCHEMA.PASSWORD_HASH: password_hash},
                where_condition={SCHEMA.USER_ID: user_id}
            )
        else:
            self.authentication_dao.new({SCHEMA.USER_ID: user_id, SCHEMA.PASSWORD_HASH: password_hash})

    def start_session(self, user_id, password):
        # TODO add "expired_on" datetime column so can be filtered by active
        # value can also be returned to client to set cookie expiry datetime.

        # Authenticate user using password.
        if self._password_valid(user_id, password):
            # Generate new session,
            session_key = Database.unique_id()
            self.sessions_dao.new({SCHEMA.USER_ID: user_id, SCHEMA.SESSION_KEY: session_key})
            return session_key
        return None

    def validate_session(self, session_key, user_id):
        # Fetch sessions for this user.
        session_rows = self.sessions_dao.read(
            None,
            where_condition={SCHEMA.SESSION_KEY: session_key},
            sortby=SCHEMA.DATE_CREATED
        )

        # Return False if no sessions have been started.
        if not session_rows:
            return False

        # Return True if latest user_id matches.
        latest_dict = Formatting.map_rows_to_schema(session_rows, self.sessions_dao.SCHEMA)[0]
        if user_id == latest_dict.get(SCHEMA.USER_ID):
            return True
        return False


class Controller:

    def __init__(self, database_file_path):

        self._database_file_path = database_file_path
        self.user_dao = UsersDAO(database_file_path)
        self.bios_dao = BiosDAO(database_file_path)
        self.experiences_dao = ExperiencesDAO(database_file_path)
        self.qualifications_dao = QualificationsDAO(database_file_path)

        self.dao_map = {
            CvParts.INFO: self.user_dao,
            CvParts.BIO: self.bios_dao,
            CvParts.EXP: self.experiences_dao,
            CvParts.QUAL: self.qualifications_dao
        }

    def get_user_data(self, user_id=None, email=None):
        user_rows = None
        if user_id:
            user_rows = self.user_dao.read(user_id, distinct=True)
        elif email:
            user_rows = self.user_dao.read(None, where_condition={SCHEMA.USER_EMAIL: email}, distinct=True)

        # Return data dictionary.
        return dict(zip(self.user_dao.SCHEMA, user_rows[0])) if user_rows else None

    def get_full_user_data(self, user_id, date_format=Formatting.DATETIME_JS_FORMAT, replace_none=False):
        # TODO Maybe formatting should be optional as edit_modal uses it to get current data and having None
        # date times would be lush.

        # Fetch user data from Users table, return None immediately if user_id is not found.
        user_dict = self.get_user_data(user_id=user_id)
        if user_dict is None:
            return None

        # Read bio and add to dictionary.
        bio_rows = self.bios_dao.read(None, where_condition={SCHEMA.USER_ID: user_id}, distinct=True)
        bio_dict = Formatting.map_rows_to_schema(bio_rows, self.bios_dao.SCHEMA)
        user_dict['bio'] = bio_dict[0] if bio_dict else None

        # Add any experiences.
        experience_rows = self.experiences_dao.read(
            None,
            where_condition={SCHEMA.USER_ID: user_id},
            sortby=SCHEMA.END_DATE
        )
        experiences_dicts = Formatting.map_rows_to_schema(experience_rows, self.experiences_dao.SCHEMA)
        formatted_experiences_dict = Formatting.format_datetime_strings_in_dict(
            experiences_dicts,
            keys=self.experiences_dao.date_time_columns,
            input_format=Formatting.DATETIME_DB_FORMAT,
            output_format=date_format,
            replace_none=replace_none
        )
        user_dict['experiences'] = formatted_experiences_dict if formatted_experiences_dict else None

        # Add any qualifications.
        qualification_rows = self.qualifications_dao.read(
            None,
            where_condition={SCHEMA.USER_ID: user_id},
            sortby=SCHEMA.END_DATE
        )
        qualification_dict = Formatting.map_rows_to_schema(qualification_rows, self.qualifications_dao.SCHEMA)
        formatted_qualification_dict = Formatting.format_datetime_strings_in_dict(
            qualification_dict,
            keys=self.qualifications_dao.date_time_columns,
            input_format=Formatting.DATETIME_DB_FORMAT,
            output_format=date_format,
            replace_none=replace_none
        )
        user_dict['qualifications'] = formatted_qualification_dict if formatted_qualification_dict else None

        return user_dict

    def new_user(self, email, display_name, title):
        # Check email has not already been used.
        user_rows = self.user_dao.read(None, where_condition={SCHEMA.USER_EMAIL: email})
        if user_rows:
            return None
        else:
            user_dict = {SCHEMA.USER_EMAIL: email, SCHEMA.USER_DISPLAY_NAME: display_name, SCHEMA.USER_TITLE: title}
            user_id = self.user_dao.new(user_dict)
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
                    where_condition = {SCHEMA.ID: validated_user_id}
                else:
                    where_condition = {SCHEMA.ID: row_id, SCHEMA.USER_ID: validated_user_id}

                dao.update(None, formatted_changes, where_condition=where_condition)

    def add(self, validated_user_id, add_dict):
        for section_name, change in add_dict.items():
            dao = self.dao_map.get(section_name)
            # TODO maybe remove all Nones, nulls and '' here.
            if dao is not None:
                # Add validated user ID as user_id
                change[SCHEMA.USER_ID] = validated_user_id
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
            # TODO Need to inforce cascade on delete for all rows with user ids. for details table (maybe rename it)
            dao.delete({SCHEMA.ID: row_id})

    def generate_edit_modal(self, edit_type, row_id, user_id):
        user_data = self.get_full_user_data(user_id=user_id)
        return HTMLModals.edit_modal(edit_type, row_id, user_data)

    def generate_manage_modal(self, user_id):
        user_data = self.get_full_user_data(user_id=user_id)
        return HTMLModals.manage_modal(user_data)

    # TODO Add this in a bit, keep it simple for now and find users by url.
    def search_user(self, search_string):
        user_rows = self.user_dao.read_like_display_name(search_string)
        if user_rows:
            # Return id, display name and title for users whose display name is like the search string
            pass
        else:
            return None


class UserAddedItems:

    def __init__(self, database_file_path):
        self.dao = UserAddedItemsDAO(database_file_path)

    def add_new(self, uai_type, uai_display_name):
        self.dao.new({'display_name': uai_display_name, 'type': uai_type, 'count': 0, 'verified': 'true'})

    def get_all(self, uai_type, verified=True):
        if verified:
            condition = {'type': uai_type, verified: 'true'}
        else:
            condition = {'type': uai_type}
        return self.dao.read(where_condition=condition)
