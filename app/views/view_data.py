import logging
from flask import Blueprint, jsonify, request
from app.views.view_helpers.view_data_helpers import execute_query_data_summary

data = Blueprint('data', __name__)
logger = logging.getLogger('main')


@data.route('/data/summary', methods=['GET'])
def view_data_summary():
    """ Returns some general information about the data set:
        - total jewels
        - total characters
        - total unique seeds
        - total unique jewels (seed/general/mf_mods)
    
    """
    response = {}

    try:
        results = execute_query_data_summary()
        response['results'] = results
    except Exception as e:
        return jsonify({'error': f'{e}'}), 500 
    
    return jsonify(response), 200


@data.route('/data/socket', methods=['GET'])
def view_data_socket_lut():
    """ Return the socket_lut table's contents. """
    pass


# maybe I'm not actually doing the lut stuff