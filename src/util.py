import glob
import logging
import os
from ConfigParser import ConfigParser

try:
    CONFIG_INI = os.path.abspath(glob.glob('mindfulness_config.ini')[0])
except:
    # try default path
    CONFIG_INI = '/opt/mindfulness/mindfulness_config.ini'


def read_config(section):
    parser = ConfigParser()
    parser.read(CONFIG_INI)
    config_params = {param[0]: param[1] for param in parser.items(section)}
    logging.info("Loaded %d parameters for section %s", len(config_params), section)
    return config_params


BASE_PATH = read_config('general')['path']
