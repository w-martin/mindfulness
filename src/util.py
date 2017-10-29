import ast
import logging
from ConfigParser import ConfigParser


def read_config(section):
    parser = ConfigParser()
    parser.read('config.ini')
    config_params = {param[0]: param[1] for param in parser.items(section)}
    logging.info("Loaded %d parameters for section %s", len(config_params), section)
    return config_params
