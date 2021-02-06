import sys

from Library.constants import SCHEMA
from Library.core import DatabaseInitiator
from Library.data import UsersDAO, AuthenticationDAO, SessionsDAO, DetailsDAO, AboutDAO, ExperiencesDAO, \
    QualificationsDAO, UserAddedItemsDAO

DB_FILE_PATH = '/Users/joshnicholls/Desktop/myCV/data.db'
DAOS = [UsersDAO, AuthenticationDAO, SessionsDAO, DetailsDAO, AboutDAO, ExperiencesDAO, QualificationsDAO, UserAddedItemsDAO]


def main():
    db_initiator = DatabaseInitiator(DB_FILE_PATH, DAOS)
    db_initiator.create_tables(parent_table=UsersDAO.TABLE, foreign_key=SCHEMA.USER)


if __name__ == '__main__':
    sys.exit(main())
