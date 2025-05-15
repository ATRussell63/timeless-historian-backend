from flask import Flask
from logging.config import dictConfig
from views.test_view import test_view


def setup_app(config):
    f = Flask(__name__)
    f.config.from_object(config)
    log_config = get_log_config(f.config)
    dictConfig(log_config)

    f.register_blueprint(test_view)

    return f


def get_log_config(log_config: dict):
    level = log_config.get('LOG_LEVEL', 'INFO')
    return {
        'version': 1,
        'formatters': {
            'base_formatter': {
                'format': log_config.get('LOG_FORMAT')
            }
        },
        'handlers': {
            'console_handler': {
                'class': 'logging.StreamHandler',
                'level': level,
                'formatter': 'base_formatter'
            }
        },
        'loggers': {
            'main': {
                'handlers': ['console_handler'],
                'level': level
            }
        }
    }