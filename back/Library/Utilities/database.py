import sqlite3
import os
import datetime
from hashlib import md5


class Database:
    ALL_CHAR = '*'
    SEPARATOR_CHAR = ','
    CONDITION_TEMPLATE = ' WHERE {}'
    QUERY_TEMPLATES = {
        'select': 'SELECT {} FROM {}{};',
        'select_distinct': 'SELECT DISTINCT {} FROM {}{};',
        'insert': 'INSERT INTO {} ({}) VALUES ({});',
        'create': 'CREATE TABLE {} ({}{});',
        'update': 'UPDATE {} SET {}{};',
        'delete': 'DELETE FROM {}{}',
        'sortby_suffix': "{} ORDER BY CASE WHEN {} IS null THEN 'ZZZZZZZZZZZZZZ' else {} END DESC",
        'cascade_suffix': ', CONSTRAINT {} FOREIGN KEY ({}) REFERENCES {}({}) ON DELETE CASCADE'
    }
    CONDITION = {
        'list': '{} in ({})',
        'single': '{} = "{}"',
        'join': ' AND '
    }
    VALUES = {
        'single': '{}={}',
        'join': ','
    }

    def __init__(self, database_file_path):
        self.file_path = database_file_path

    @staticmethod
    def _parse_where_dict(where_dict):
        where_list = []
        for column, value in where_dict.items():
            if isinstance(value, list):
                where_list.append(Database.CONDITION.get('list').format(column, ','.join(value)))
            else:
                where_list.append(Database.CONDITION.get('single').format(column, value))
        if where_list:
            return Database.CONDITION.get('join').join(where_list)
        return ''

    @staticmethod
    def _generate_condition(condition):
        if condition is None:
            return ''
        if isinstance(condition, dict):
            condition = Database._parse_where_dict(condition)
        return Database.CONDITION_TEMPLATE.format(condition)

    @staticmethod
    def _generate_columns(values):
        if values is None:
            return Database.ALL_CHAR
        elif isinstance(values, dict):
            values_list = ['"{}"={}'.format(c, Database._clean_string(v)) for c, v in values.items()]
        elif not isinstance(values, list):
            values_list = [values]
        else:
            values_list = values
        return Database.VALUES.get('join').join(values_list)


    @staticmethod
    def _clean_string(dirty_string):
        if dirty_string is None:
            dirty_string = 'null'
        else:
            dirty_string = str(dirty_string)
        clean_string = dirty_string.replace('"', "'")
        return '"{}"'.format(clean_string)

    @staticmethod
    def unique_id(salt=None):
        to_hash = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        to_hash = to_hash + str(salt) if salt is not None else to_hash
        hash_obj = md5(to_hash.encode())
        return hash_obj.hexdigest()

    def create_table(self, name, schema, primary_key='id', foreign_table=None, foreign_key=None):
        def is_primary_key(key):
            if key == primary_key:
                return 'PRIMARY KEY'
            else:
                return ''

        columns = ','.join(['{} {} {}'.format(k, 'TEXT', is_primary_key(k)) for k in schema])
        if foreign_key in schema and foreign_table is not None:
            fk_name = 'fk_{}_{}'.format(name, foreign_key).lower()
            cascade = Database.QUERY_TEMPLATES.get('cascade_suffix').format(fk_name, foreign_key, foreign_table, primary_key)
        else:
            cascade = ''
        sql = Database.QUERY_TEMPLATES.get('create').format(name, columns, cascade)
        self.execute_sql(sql_query=sql)

    def execute_sql(self, sql_query=None, sql_query_list=None):
        if sql_query is None and sql_query_list is None:
            raise Exception('execute_sql can only take either sql_query or sql_query_list, not both.')
        with sqlite3.connect(self.file_path) as connection:
            cursor = connection.cursor()
            if sql_query:
                cursor.execute(sql_query)
                return cursor.fetchall()
            else:
                results = []
                for sql_query in sql_query_list:
                    cursor.execute(sql_query)
                    results.append(cursor.fetchall())
                return results

    def select(self, table, columns=None, condition=None, sortby=None, distinct=False, return_sql=False):
        query_template = self.QUERY_TEMPLATES.get('select_distinct') if distinct else self.QUERY_TEMPLATES.get('select')
        condition_string = self._generate_condition(condition)
        if sortby is not None:
            condition_string = self.QUERY_TEMPLATES.get('sortby_suffix').format(condition_string, sortby, sortby)
        sql = query_template.format(
            self._generate_columns(columns),
            table,
            condition_string
        )
        return sql if return_sql else self.execute_sql(sql_query=sql)

    def insert(self, table, values, return_sql=False):
        columns = Database.VALUES.get('join').join(values.keys())
        values = Database.VALUES.get('join').join(['null' if v is None else '"{}"'.format(v) for v in list(values.values())])
        sql = self.QUERY_TEMPLATES.get('insert').format(table, columns, values)
        return sql if return_sql else self.execute_sql(sql_query=sql)

    def insert_multiple(self, table, rows):
        sql_queries = [self.insert(table, values, return_sql=True) for values in rows]
        self.execute_sql(sql_query_list=sql_queries)

    def update(self, table, values_dict, condition, return_sql=False):
        sql = self.QUERY_TEMPLATES.get('update').format(
            table,
            self._generate_columns(values_dict),
            self._generate_condition(condition)
        )
        return sql if return_sql else self.execute_sql(sql_query=sql)

    def delete(self, table, condition, return_sql=False):
        sql = self.QUERY_TEMPLATES.get('delete').format(
            table,
            self._generate_condition(condition)
        )
        return sql if return_sql else self.execute_sql(sql_query=sql)


class DatabaseInitiator:

    def __init__(self, database_file_path, daos):
        self.database_file_path = database_file_path
        self.daos = daos

    def create_tables(self, foreign_key=None, parent_table=None):
        # Open new database file.
        if not os.path.isfile(self.database_file_path):
            with open(self.database_file_path, 'w+'):
                pass
            print('Created database file "{}".'.format(self.database_file_path))

        # Create tables.
        for dao in self.daos:
            try:
                if dao.TABLE == parent_table:
                    dao(self.database_file_path).create_table()
                else:
                    dao(self.database_file_path).create_table(foreign_key=foreign_key, parent_table=parent_table)

            except sqlite3.OperationalError as e:
                print('WARNING: Could not create table "{}". SQL Error: "{}"'.format(dao.TABLE, e))