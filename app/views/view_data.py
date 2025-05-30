import logging
from flask import Blueprint, jsonify, request
from app.views.view_helpers.view_data_helpers import execute_query_data_summary, execute_query_fetch_random_jewels, request_all
from app.views.view_helpers.view_search_helpers import format_jewel_search_results

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


@data.route('/data/sample', methods=['GET'])
def view_data_sample():
    """ Returns an assortment of random jewels.
    """

    response = {}
    try:
        limit = int(request.args.get('limit'))
        if limit < 1 or limit > 50:
            return jsonify({'error': 'Invalid limit argument. Limit must be between 1-50'}), 400

        data = execute_query_fetch_random_jewels(limit)
        response['results'] = format_jewel_search_results(data, request_all)
    except Exception as e:
        return jsonify({'error': f'{e}'}), 500

    return jsonify(response), 200 


@data.route('/data/socket', methods=['GET'])
def view_data_socket_lut():
    """ Return the socket_lut table's contents. """
    pass


# maybe I'm not actually doing the lut stuff