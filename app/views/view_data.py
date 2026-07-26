import logging
from flask import Blueprint, jsonify, request
from app.views.view_helpers.view_data_helpers import execute_query_data_summary, execute_query_fetch_random_jewels, \
    request_all, execute_query_fetch_latest_jewel, execute_query_get_joats, format_get_joats_results, \
    execute_query_vips_for_league, format_vips_for_league_results, execute_query_histogram_data, \
    format_histogram_results, execute_query_class_affinities, format_class_affinities_results
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

        query_results = execute_query_fetch_random_jewels(limit)
        response['results'] = format_jewel_search_results(query_results, request_all)
    except Exception as e:
        return jsonify({'error': f'{e}'}), 500

    return jsonify(response), 200 


@data.route('/data/latest', methods=['GET'])
def view_data_latest_jewel():
    """ Return the latest jewel added to the database. """
    
    logger.debug('/data/latest')
    response = {}
    try:
        query_results = execute_query_fetch_latest_jewel()
        response['results'] = format_jewel_search_results(query_results)
    
    except Exception as e:
        return jsonify({'error': f'{e}'}), 500

    return jsonify(response), 200

@data.route('/data/joats', methods=['GET'])
def view_data_joats():
    """
    Returns the most used (jewel, seed, socket_id) of each league, and of all time.

    Params:
        - limit: int
    """
    logger.debug('/data/joats')
    response = {}
    try:
        limit = int(request.args.get('limit'))
        if limit < 1:
            return jsonify({'error': 'Invalid limit argument. Limit must be a positive integer.'}), 400

        query_results = execute_query_get_joats()
        response['results'] = format_get_joats_results(query_results)
    except Exception as e:
        return jsonify({'error': f'{e}'}), 500

    return jsonify(response), 200

@data.route('/data/vips', methods=['POST'])
def view_data_vips():
    """
    Returns the characters for each member of the VIP list in the given leagues.

    Request:
    {
        "leagues": ["Mirage", "Hardcore Mirage"]
    }
    """
    logger.debug('/data/vips')
    response = {}
    try:
        leagues = request.get_json().get('leagues')
        if leagues is None or len(leagues) == 0:
            return jsonify({'error': 'Request must include at least one league to query.'}), 400

        query_results = execute_query_vips_for_league(leagues)
        response['results'] = format_vips_for_league_results(query_results)
    except Exception as e:
        return jsonify({'error': f'{e}'}), 500

    return jsonify(response), 200

@data.route('/data/general_hist', methods=['GET'])
def view_data_general_histogram():
    """
    Returns data to draw a histogram representing the usage of each keystone during each league.
    """
    # TODO - maybe I add the date range for the league as well, but I think that would muddle the graph idk

    logger.debug('/data/general_hist')
    response = {}
    try:
        query_results = execute_query_histogram_data()
        response['results'] = format_histogram_results(query_results)
    except Exception as e:
        return jsonify({'error': f'{e}'}), 500

    return jsonify(response), 200

@data.route('/data/class_aff', methods=['GET'])
def view_data_class_affinities():
    """
    Returns a ranking of the most used keystones for each ascendancy.
    """

    logger.debug('/data/class_aff')
    response = {}
    try:
        limit = int(request.args.get('limit'))
        if limit < 1:
            return jsonify({'error': 'Invalid limit argument. Limit must be a positive integer.'}), 400

        query_results = execute_query_class_affinities(limit)
        response['results'] = format_class_affinities_results(query_results)
    except Exception as e:
        return jsonify({'error': f'{e}'}), 500

    return jsonify(response), 200


