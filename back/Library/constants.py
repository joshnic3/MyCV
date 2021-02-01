
class CvParts:

    INFO = 'details'
    BIO = 'bio'
    EXP = 'experiences'
    QUAL = 'qualifications'
    AUTH = 'authentication'


class CookieNames:

    SESSION_KEY = 'session_key'
    USER_ID = 'user_id'


class SCHEMA:

    ID = 'id'
    USER_ID = 'user_id'
    USER_HIDDEN = 'hidden'

    START_DATE = 'start_date'
    END_DATE = 'end_date'
    DATE_CREATED = 'created_date'
    LAST_CHANGED = 'last_change'

    USER_EMAIL = 'email'
    USER_DISPLAY_NAME = 'display_name'
    USER_TITLE = 'title'

    CONTENT = 'text'

    EXP_EMPLOYER = 'employer_id'
    EXP_ROLE = 'position'

    QUAL_SCHOOL = 'school_id'
    QUAL_SUBJECT = 'level'
    # QUAL_GRADE = 'level'

    SESSION_KEY = 'session_key'
    PASSWORD_HASH = 'password'


class Mapping:
    WHERE = 'where'
    WHAT = 'what'
    GRADE = 'grade'
    START_DATE = 'start_date'
    END_DATE = 'end_date'
    CONTENT = 'text'

    KEYS = [WHERE, WHAT, GRADE, START_DATE, END_DATE, CONTENT]
    CAN_DELETE = [CvParts.EXP, CvParts.QUAL]

    # SCHEMA AND DISPLAY_NAME HAVE TO HAVE SAME MAPPING
    SCHEMA = {
        CvParts.INFO: {
            WHERE: SCHEMA.USER_DISPLAY_NAME,
            WHAT: SCHEMA.USER_TITLE,
        },
        CvParts.BIO: {
            CONTENT: SCHEMA.CONTENT,
        },
        CvParts.EXP: {
            WHERE: SCHEMA.EXP_EMPLOYER,
            WHAT: SCHEMA.EXP_ROLE,
            START_DATE: SCHEMA.START_DATE,
            END_DATE: SCHEMA.END_DATE,
            CONTENT: SCHEMA.CONTENT
        },
        CvParts.QUAL: {
            WHERE: SCHEMA.QUAL_SCHOOL,
            WHAT: SCHEMA.QUAL_SUBJECT,
            START_DATE: SCHEMA.START_DATE,
            END_DATE: SCHEMA.END_DATE,
            CONTENT: SCHEMA.CONTENT
            # GRADE: SCHEMA.QUAL_GRADE
        }
    }

    DISPLAY_NAME = {
        CvParts.INFO: {
            WHERE: 'Display Name',
            WHAT: 'Headline',
        },
        CvParts.BIO: {
            CONTENT: 'About',
        },
        CvParts.EXP: {
            WHERE: 'Company',
            WHAT: 'Position',
            START_DATE: 'Start Date',
            END_DATE: 'End Date',
            CONTENT: 'Details',
        },
        CvParts.QUAL: {
            WHERE: 'School',
            WHAT: 'Subject',
            GRADE: 'Grade',
            START_DATE: 'Start Date',
            END_DATE: 'End Date',
            CONTENT: 'Details',
        }
    }

    SECTION_TITLE = {
        CvParts.EXP: 'Experience',
        CvParts.QUAL: 'Qualification'
    }
