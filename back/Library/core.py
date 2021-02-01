import argparse
import csv
import datetime
import logging
import os
import sqlite3
from hashlib import md5

import yaml

from Library import constants
from Library.constants import SCHEMA


def write_rows_to_csv(csv_file_path, rows, headers=None):
    rows_to_write = [headers] + rows if headers else rows
    with open(csv_file_path, 'w') as csv_file:
        writer = csv.writer(csv_file)
        for row in rows_to_write:
            writer.writerow(row)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--configs', type=str, required=True)
    arguments = parser.parse_args()
    return arguments


class Constants:
    DATETIME_DB_FORMAT = '%Y%m%d'


# TODO There is some refactoring to be done here.
class Formatting:

    NONE_STRING = 'Present'
    DATETIME_DB_FORMAT = '%Y%m%d%H%M%S'
    DATETIME_JS_FORMAT = '%Y-%m-%d'
    DATETIME_PP_FORMAT = '%d/%m/%Y'

    @staticmethod
    def format_datetime_strings_in_dict(data_dicts, keys=None, input_format=None, output_format=None,
                                        replace_none=False):

        if isinstance(data_dicts, list):
            return_list = True
        else:
            return_list = False
            data_dicts = [data_dicts]

        for data_dict in data_dicts:
            # Turn all strings to date times. Only look at keys list, but do all if empty.
            if input_format:
                if keys:
                    for key in keys:
                        datetime_string = data_dict.get(key)
                        if datetime_string:
                            data_dict[key] = datetime.datetime.strptime(datetime_string, input_format)

            if output_format:
                if keys:
                    for key in keys:
                        data_dict[key] = Formatting.datetime_to_string(
                            data_dict.get(key),
                            format_string=output_format,
                            replace_none=replace_none
                        )
        if return_list:
            return data_dicts
        return data_dicts[0]

    @staticmethod
    def map_rows_to_schema(rows, schema):
        return [dict(zip(schema, r)) for r in rows]

    @staticmethod
    def datetime_to_string(datetime_obj, format_string=None, replace_none=False):
        format_string = Formatting.DATETIME_DB_FORMAT if format_string is None else format_string
        if datetime_obj is None:
            if replace_none:
                return Formatting.NONE_STRING
            else:
                return None
        else:
            return datetime_obj.strftime(format_string)

    @staticmethod
    def remove_nones_from_dict(dict_to_process):
        none_strings = ['', 'null']
        dict_to_return = {}
        for key, value in dict_to_process.items():
            if value and value not in none_strings:
                dict_to_return[key] = value
        return dict_to_return


class Logger:

    @staticmethod
    def new(log_file_path, production=True, debug=False):
        # Setup logging to file.
        logging.root.handlers = []
        log_format = '%(asctime)s|%(levelname)s : %(message)s'
        if debug:
            logging.basicConfig(level='DEBUG', format=log_format, filename=log_file_path)
        else:
            logging.basicConfig(level='INFO', format=log_format, filename=log_file_path)
        log = logging.getLogger('')

        # Setup logging to console.
        if not production:
            console = logging.StreamHandler()
            formatter = logging.Formatter(log_format)
            console.setFormatter(formatter)
            logging.getLogger('').addHandler(console)
        return log

    @staticmethod
    def generate_log_path(sc, script_name):
        date_string = sc.get_runtime(as_string=True)[:-6]
        time_string = sc.get_runtime(as_string=True)[8:]
        log_file_name = '{}_{}_{}.log'.format(script_name[:-3], date_string, time_string)
        return os.path.join(sc.paths.get('log'), log_file_name)


class ScriptConfiguration:

    def __init__(self, config_file_path=None):
        self._runtime = datetime.datetime.now()
        self.environment = None
        self.paths = {}
        self.params = {}

        # Read configs from YAML file if provided.
        if config_file_path:
            self._read_yaml_config_file(config_file_path)

    def _read_yaml_config_file(self, config_file_path):
        with open(config_file_path) as yaml_file:
            global_configs = yaml.load(yaml_file, Loader=yaml.FullLoader)
            self.environment = global_configs.get('environment', self.environment)
            self.paths = global_configs.get('paths', self.paths)
            self.params = global_configs.get('params', self.params)

    def pp_params(self, script_name=None):
        template = '"{}" started with parameters: {}'
        default = {'environment': self.environment}
        params = {**default, **self.params}
        params_as_string = ', '.join(['{}: {}'.format(p, params.get(p)) for p in params])
        return template.format(script_name if script_name else 'Script', params_as_string)

    def is_production(self):
        return True if self.environment == 'production' else False

    def get_runtime(self, as_string=False):
        if as_string:
            return self._runtime.strftime(constants.DATETIME.FORMAT)
        return self._runtime


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
        if foreign_key is not None and foreign_table is not None:
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
