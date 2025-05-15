import logging
from flask import Blueprint, jsonify, request

test_view = Blueprint('test_view', __name__)
logger = logging.getLogger('main')

@test_view.route('/test', methods=['GET', 'POST'])
def view_test():
    print('first, a little test to make sure flask can launch at all')
    return jsonify({'status': 'Success'}, 200)
