import logging
from flask import Blueprint, jsonify, request
from app.views.view_helpers.view_data_helpers import execute_query_data_summary, execute_query_fetch_random_jewels, \
    request_all, execute_query_fetch_latest_jewel
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
    logger.debug('/data/summary')

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
    logger.debug('/data/sample')
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


@data.route('/data/latest', methods=['GET'])
def view_data_latest_jewel():
    """ Return the latest jewel added to the database. """
    
    logger.debug('/data/latest')
    response = {}
    try:
        data = execute_query_fetch_latest_jewel()
        response['results'] = format_jewel_search_results(data)
    
    except Exception as e:
        return jsonify({'error': f'{e}'}), 500

    return jsonify(response), 200