import os

from create_app import setup_app
from app_config import create_config

config_path = os.environ.get('APP_CONFIG', '')
config = create_config(config_path)
app = setup_app(config)

port = os.environ.get('FLASK_PORT')

if __name__ == '__main__':
    app.run(host='localhost', port=port)