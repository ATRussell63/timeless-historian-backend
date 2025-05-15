import configparser
import os
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger('main')


@dataclass
class AppConfig:
    DEBUG: bool
    LOG_LEVEL: str
    LOG_FORMAT: str
    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    SQLALCHEMY_ECHO: bool
    API_BASE_URL: str
    SITE_BASE_URL: str
    LADDER_MAX: int


APP_CONFIG = Optional[AppConfig]
APP_CONFIG = None


def get_config() -> AppConfig:
    if APP_CONFIG is None:
        raise Exception('Config not found!')
    return APP_CONFIG


def create_config(file_path: str = None) -> AppConfig:
    global APP_CONFIG

    if not APP_CONFIG:
        parser = configparser.ConfigParser()
        files_read = parser.read(file_path or os.environ['APP_CONFIG'])
        logger.debug(f'Config read from {files_read}')

        if not file_path:
            print('Config using environment vars')
        else:
            print(f'Config parser using {file_path}')

        APP_CONFIG = AppConfig(
            parser.getboolean('APP', 'DEBUG'),
            parser.get('APP', 'LOG_LEVEL'),
            parser.get('APP', 'LOG_FORMAT'),
            parser.get('DB', 'DATABASE_HOST'),
            parser.get('DB', 'DATABASE_PORT'),
            parser.get('DB', 'DATABASE_USER'),
            parser.get('DB', 'DATABASE_PASSWORD'),
            parser.get('DB', 'DATABASE_NAME'),
            parser.getboolean('DB', 'SQLALCHEMY_ECHO'),
            parser.get('GGG', 'API_BASE_URL'),
            parser.get('GGG', 'SITE_BASE_URL'),
            parser.getint('GGG', 'LADDER_MAX')
        )

    return APP_CONFIG
