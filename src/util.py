import logging
import os
from ConfigParser import ConfigParser

CONFIG_INI = os.path.join(os.pardir, 'config.ini')


def read_config(section):
    parser = ConfigParser()
    parser.read(CONFIG_INI)
    config_params = {param[0]: param[1] for param in parser.items(section)}
    logging.info("Loaded %d parameters for section %s", len(config_params), section)
    return config_params


BASE_PATH = read_config('general')['path']
