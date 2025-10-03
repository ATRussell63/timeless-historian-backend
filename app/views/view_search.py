import logging
from flask import Blueprint, jsonify, request
from .view_helpers.view_search_helpers import parse_jewel_search_request, perform_jewel_search, format_jewel_search_results, \
    parse_bulk_query, perform_bulk_overview, format_bulk_overview_results

search = Blueprint('search', __name__)
logger = logging.getLogger('main')


@search.route('/search', methods=['POST'])
def view_search():
    """
    Search for jewels that meet the given criterion.
    We accept all the data to perform an exact match search,
    however general and mf mods are only used to label the data.

    The frontend is intended to filter the search results as desired.

    Request: 
    {
        jewel_type: str,
        seed: int,
        general: str
        ?mf_mods: [str, str]
    }

    Response:
    {
        leagues: [
            'Settlers': [

            ]
        ]
    }

    """
    logger.debug(f'/search received: {request.json}')

    response_body = {}
    try:
        request_data = parse_jewel_search_request(request)
        raw_search_results = perform_jewel_search(request_data)
        response_body['results'] = format_jewel_search_results(raw_search_results, request_data)
    except Exception as e:
        return jsonify({'error': f'{e}'}), 500

    return jsonify(response_body), 200


@search.route('/search/bulk', methods=['POST'])
def view_bulk_overview():
    """
        Accepts a list of jewels and returns broad information about what results they generated.

        Request:
        jewels: [
            {
                i: 0    # index (yeah kinda redundant)
                x: int, # coords for where the jewel is in the tab
                y: int,
                jewel_type: str,
                seed: int,
                general: str,
                ?mf_mods: [str, str]
            }...
        ]
    """

    logger.debug(f'/search/bulk received: {request.json}')

    response_body = {}
    try:
        bulk_request_data = parse_bulk_query(request)
        overview_query_results = perform_bulk_overview(bulk_request_data)
        response_body = format_bulk_overview_results(bulk_request_data, overview_query_results)
    except Exception as e:
        return jsonify({'error': f'{e}'}), 500

    return jsonify(response_body), 200