import configparser
import glob
import logging
import os
import subprocess
from contextlib import contextmanager

try:
    CONFIG_INI = os.path.abspath(glob.glob('mindfulness_config.ini')[0])
except:
    # try default path
    CONFIG_INI = '/opt/mindfulness/mindfulness_config.ini'

CONFIG_PARSER = None
DEFAULT_PORT = 8484


def get_config_parser():
    global CONFIG_PARSER
    if CONFIG_PARSER is None:
        CONFIG_PARSER = configparser.ConfigParser()
        CONFIG_PARSER.read(CONFIG_INI)
    return CONFIG_PARSER


def read_config(section, item, type=str, default=None):
    config_parser = get_config_parser()
    if type is int:
        result = config_parser.getint(section, item, fallback=default)
    elif type is float:
        result = config_parser.getfloat(section, item, fallback=default)
    elif type is bool:
        result = config_parser.getboolean(section, item, fallback=default)
    else:
        result = config_parser.get(section, item, fallback=default)

    logging.debug("Loaded config setting {} - {}: {}".format(section, item, result))
    return result


BASE_PATH = read_config('general', 'path')


def remove_commas_from_string(input_string):
    return input_string.replace(',', '')


def get_user_cycle_days():
    return read_config('general', 'cycle_user_days', type=int, default=14)


def get_played_cycle_days():
    return read_config('general', 'repeat_min_wait_days', type=int, default=365)


def get_title_from_youtube_url(url):
    try:
        output = str(subprocess.check_output(['youtube-dl', '--get-title', url, '--no-warnings'],
                                             stderr=subprocess.STDOUT)).strip()
    except subprocess.CalledProcessError as ex:
        output = str(ex.output).strip()
    except OSError as ex:
        output = 'youtube-dl not found: %s' % ex
    except Exception as ex:
        output = 'Something bad happened: %s' % ex
    return remove_commas_from_string(output)


@contextmanager
def chdir(path):
    cwd = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(cwd)
