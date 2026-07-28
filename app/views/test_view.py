import logging
from flask import Blueprint

test_view = Blueprint('test_view', __name__)
logger = logging.getLogger('main')