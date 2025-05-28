from flask import Flask
from flask_cors import CORS
from flask_compress import Compress
from logging.config import dictConfig
from app.views.test_view import test_view
from app.views.view_search import search
from app.views.view_data import data


def setup_app(config):
    f = Flask(__name__)
    CORS(f)
    Compress(f)
    f.config.from_object(config)
    log_config = get_log_config(f.config)
    dictConfig(log_config)

    f.register_blueprint(test_view)
    f.register_blueprint(search)
    f.register_blueprint(data)

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