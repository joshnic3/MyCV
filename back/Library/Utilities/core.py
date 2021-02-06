import argparse
import datetime
import logging
import os

import yaml

from Library import constants


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

    def _parse_arguments(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--configs', type=str, required=True)
        arguments = parser.parse_args()
        return arguments

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



