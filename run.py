import os

from app.create_app import setup_app
from app.app_config import create_config

config_path = os.environ.get('APP_CONFIG', './config/config.ini')
config = create_config(config_path)
app = setup_app(config)

port = os.environ.get('FLASK_PORT', 5000)

if __name__ == '__main__':
    app.run(host='localhost', port=port)