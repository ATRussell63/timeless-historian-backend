import logging
from flask import Blueprint, jsonify
from sqlalchemy.sql import select
from app.views.view_helpers.view_search_helpers import query_jewel_search, SearchRequest, format_jewel_search_results, mml1, mml2
from app.db import get_engine

test_view = Blueprint('test_view', __name__)
logger = logging.getLogger('main')


def query_fetch_all_jewels(search_request):
    """Reformat the search query, replacing the where clause but keep everything else identical."""

    q = query_jewel_search(search_request)

    q = select(*q.selected_columns).select_from(q.get_final_froms()[0]).order_by(*q._order_by_clause)
    q = q.where(mml1.c.mod_text == search_request.mf_mods[0])
    q = q.where(mml2.c.mod_text == search_request.mf_mods[1])

    return q


def fetch_all_jewels(query):
    with get_engine().connect() as conn:
        results = conn.execute(query)
        return results


@test_view.route('/test', methods=['GET', 'POST'])
def view_test():
    """
        Return all jewels in the db for ui testing purposes.
    """
    
    bogus_search_params = SearchRequest(
        jewel_type='Militant Faith',
        seed=12345,
        general='Borgus',
        mf_mods=['1% reduced Mana Cost of Skills per 10 Devotion',
                 '+2% to all Elemental Resistances per 10 Devotion']
    )

    response = {}
    try:
        q = query_fetch_all_jewels(bogus_search_params)
        data = fetch_all_jewels(q)
        response['results'] = format_jewel_search_results(data, bogus_search_params)

    except Exception as e:
        return jsonify({'error': f'{e}'}), 500

    return jsonify(response), 200


# TODO - delete this shit later or something
@test_view.route('/test/manual', methods=['GET', 'POST'])
def view_test_manual_data():
    """
        Return a manual subset of the data.
    """
    from app.views.view_helpers.view_test_view_helpers import all_data_response
    return jsonify(all_data_response), 200