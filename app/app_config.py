import configparser
import os
import logging
import re
from dataclasses import dataclass
from typing import Optional, List

logger = logging.getLogger('main')


@dataclass
class AppConfig:
    DEBUG: bool
    LOG_LEVEL: str
    LOG_FORMAT: str
    DATA_DIR: str
    LEVEL_CUTOFF: int
    MAX_PROCESSED_CHARACTERS: int
    LIVE_LEAGUES: List[str]
    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    SQLALCHEMY_ECHO: bool
    LIVE_PATCH: str
    API_BASE_URL: str
    SITE_BASE_URL: str
    LADDER_MAX: int


APP_CONFIG = Optional[AppConfig]
APP_CONFIG = None


def get_config() -> AppConfig:
    if APP_CONFIG is None:
        raise Exception('Config not found!')
    return APP_CONFIG


def init_logger(level: str, fmt: str):
    logging.basicConfig(level=level,
                        format=fmt)


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
            parser.get('APP', 'DATA_DIR'),
            parser.getint('APP', 'LEVEL_CUTOFF'),
            parser.getint('APP', 'MAX_PROCESSED_CHARACTERS'),
            [re.sub('_', ' ', league) for league in parser.get('APP', 'LIVE_LEAGUES').split(',')],
            parser.get('DB', 'DATABASE_HOST'),
            parser.get('DB', 'DATABASE_PORT'),
            parser.get('DB', 'DATABASE_USER'),
            parser.get('DB', 'DATABASE_PASSWORD'),
            parser.get('DB', 'DATABASE_NAME'),
            parser.getboolean('DB', 'SQLALCHEMY_ECHO'),
            parser.get('GGG', 'LIVE_PATCH'),
            parser.get('GGG', 'API_BASE_URL'),
            parser.get('GGG', 'SITE_BASE_URL'),
            parser.getint('GGG', 'LADDER_MAX'),
        )

        init_logger(APP_CONFIG.LOG_LEVEL, APP_CONFIG.LOG_FORMAT)

    return APP_CONFIG


def get_data_path():
    try:
        config = get_config()
        return f'{config.DATA_DIR}/{config.LIVE_PATCH}/'
    except Exception:
        # VSCode is so retarded but so am I so I guess we're even
        logger.error('ALARMA, THE LOG FILE IS BORKED')
        return ''