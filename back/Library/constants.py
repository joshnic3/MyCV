class CookieNames:

    SESSION_KEY = 'session_key'
    USER_ID = 'user_id'


class Component:

    USER = 'user'
    AUTHENTICATION = 'authentication'
    DETAILS = 'details'
    ABOUT = 'about'
    EXPERIENCE = 'experience'
    QUALIFICATION = 'qualification'

    CAN_DELETE = [EXPERIENCE, QUALIFICATION]


class Key:
    TITLE = 'title'
    H1 = 'header_1'
    H2 = 'header_2'
    START = 'start_date'
    END = 'end_date'
    TEXT = 'text'

    TO_DISPLAY = [H1, H2, START, END, TEXT]


class Schema:

    ID = 'id'
    USER = 'user_id'
    EMAIL = 'email'
    NAME = 'display_name'

    # Small Bespoke Text.
    HIDDEN = 'hidden'
    SESSION_KEY = 'session_key'
    PASSWORD_HASH = 'password_hash'
    TYPE = 'type'

    # TODO These 2 could be different data types but i dont want to worry about that atm
    COUNT = 'count'
    VERIFIED = 'verified'

    # User Added Items.
    EMPLOYER = 'employer_id'
    ROLE = 'role_id'
    SCHOOL = 'school_id'
    SUBJECT = 'subject_id'

    # Dates
    START = 'start_date'
    END = 'end_date'
    CREATED = 'created_date'
    LAST_CHANGED = 'last_change_date'
