import logging
from typing import List
import copy

from app.db import get_engine
from app.models import c_, l_, j_, jtl_, gl_, mml_, cl_, sl_, v_
from sqlalchemy.sql import select, func, distinct, alias, table, column
from sqlalchemy import text, cast, literal_column, and_, tuple_, Row, case, literal
from app.views.view_helpers.view_search_helpers import query_jewel_search, query_fetch_latest_jewel, \
    SearchRequest, mml1, mml2, base_jewel_query, format_jewel_search_results

logger = logging.getLogger('main')

def query_data_summary():
    q = select(func.count('*').label('total_jewels'),
               func.count(distinct(c_.c.character_id)).label('total_characters'),
               func.count(distinct(j_.c.seed)).label('unique_seeds'),
               func.count(distinct(tuple_(j_.c.seed, j_.c.general_id, j_.c.mf_mods))).label('unique_jewels')) \
        .join_from(j_, c_, j_.c.character_id == c_.c.character_id)
    
    return q


def execute_query_data_summary() -> dict:
    q = query_data_summary()
    with get_engine().connect() as conn:
        results = conn.execute(q).first()
        return results._asdict()


request_all = SearchRequest(jewel_type='Militant Faith', seed=0, general='', mf_mods=['1% reduced Mana Cost of Skills per 10 Devotion', '+2% to all Elemental Resistances per 10 Devotion'])


def query_fetch_random_jewels(limit: int):

    q = query_jewel_search(request_all)

    # pop the mf mod columns and spoof them to false, 0, etc
    
    q = select(*q.selected_columns).select_from(q.get_final_froms()[0])
    q = q.where(mml1.c.mod_text == request_all.mf_mods[0])
    q = q.where(mml2.c.mod_text == request_all.mf_mods[1])
    q = q.order_by(func.random()).limit(limit)
    return q


def execute_query_fetch_random_jewels(limit: int):
    q = query_fetch_random_jewels(limit)
    with get_engine().connect() as conn:
        results = conn.execute(q)
        return results


def execute_query_fetch_latest_jewel():
    q = query_fetch_latest_jewel()
    with get_engine().connect() as conn:
        results = conn.execute(q)
        return results

def query_get_joats():
    """
    Returns the most used (jewel, seed, socket) tuple of each league.
    Essentially the rosetta stone for determining which seed the stat stackers are using.
    """

    counts = (
        select(
            func.count(func.distinct(c_.c.ggg_id)).label("total"),
            j_.c.seed,
            j_.c.socket_id,
            sl_.c.node_id,
            sl_.c.pob_name,
            sl_.c.description,
            jtl_.c.type_name,
            case(
                (func.grouping(l_.c.league_name) == 1, literal("ALL")),
                else_=l_.c.league_name,
            ).label("league_name"),
            case(
                (func.grouping(l_.c.hardcore) == 1, literal(False)),
                else_=l_.c.hardcore,
            ).label("hardcore"),
        )
        .select_from(
            j_
            .join(jtl_, j_.c.jewel_type_id == jtl_.c.jewel_type_id)
            .join(c_, j_.c.character_id == c_.c.character_id)
            .join(l_, c_.c.league_id == l_.c.league_id)
            .join(sl_, sl_.c.socket_id == j_.c.socket_id)
        )
        .group_by(
            func.grouping_sets(
                tuple_(
                    j_.c.seed,
                    j_.c.socket_id,
                    sl_.c.node_id,
                    sl_.c.pob_name,
                    sl_.c.description,
                    jtl_.c.type_name,
                    l_.c.league_name,
                    l_.c.hardcore,
                ),
                tuple_(
                    j_.c.seed,
                    j_.c.socket_id,
                    j_.c.socket_id,
                    sl_.c.node_id,
                    sl_.c.pob_name,
                    sl_.c.description,
                    jtl_.c.type_name,
                ),
            )
        )
        .having(func.count(func.distinct(c_.c.ggg_id)) > 1)
        .cte("counts")
    )

    ranked = (
        select(
            counts,
            func.row_number()
            .over(
                partition_by=counts.c.league_name,
                order_by=counts.c.total.desc(),
            )
            .label("rn"),
        )
        .cte("ranked")
    )

    query = (
        select(
            ranked.c.rn.label('rank'),
            ranked.c.total,
            ranked.c.seed,
            ranked.c.socket_id,
            ranked.c.node_id,
            ranked.c.pob_name.label("socket_name"),
            ranked.c.description.label("socket_description"),
            ranked.c.type_name,
            ranked.c.league_name,
            ranked.c.hardcore,
        )
        .where(ranked.c.rn <= 10)
        .order_by(
            case((ranked.c.league_name == "ALL", 0), else_=1),
            ranked.c.league_name,
            ranked.c.rn,
        )
    )

    return query

def execute_query_get_joats():
    q = query_get_joats()
    with get_engine().connect() as conn:
        results = conn.execute(q)
        return results

def format_get_joats_results(query_results: List[Row]) -> dict:
    """
    {
        "ALL": {
            'hardcore': false,
            'jewels': [
                {
                    'rank': 1,
                    'total': 72,
                    'seed': 12345,
                    'socket_id': 16,
                    'socket_name': 'Marauder',
                    'socket_description': 'Marauder',
                    'type_name': 'Lethal Pride'
                }
            ]
        },
        "Mirage": ...
    }
    """

    # TODO - maybe add league_active but also maybe not
    output = {}

    for row in query_results.mappings():
        formatted_row = copy.deepcopy(dict(row))

        league_name = formatted_row['league_name']
        if output.get(league_name) is None:
            output[league_name] = {}
            output[league_name]['hardcore'] = formatted_row['hardcore']
            output[league_name]['jewels'] = []

        formatted_row.pop('league_name')
        formatted_row.pop('hardcore')
        output[league_name]['jewels'].append(formatted_row)

    return output

def query_vips_for_league(leagues: List[str]):
    """
    Get the VIP characters for the given league.
    """

    query = (base_jewel_query()
             .where((v_.c.account_name.is_not(None)) & (l_.c.league_name.in_(leagues)))
             .order_by(v_.c.nickname))

    return query

def execute_query_vips_for_league(leagues: List[str]):
    q = query_vips_for_league(leagues)
    with get_engine().connect() as conn:
        results = conn.execute(q)
        return results

def format_vips_for_league_results(query_results: List[Row]) -> dict:
    return format_jewel_search_results(query_results)

def query_histogram_data():
    """
    Returns a count of how many scanned jewels had each general in each league,
    as well as the totals for each league for ease of use.
    """

    counts_query = select(func.count().label('total'),
                   jtl_.c.type_name.label('type_name'),
                   gl_.c.general_name.label('general_name'),
                   gl_.c.keystone_name.label('keystone_name'),
                   l_.c.league_name.label('league_name'),
                   l_.c.league_id.label('league_id'),
                   l_.c.hardcore.label('hardcore')) \
             .join_from(j_, c_, j_.c.character_id == c_.c.character_id) \
             .join(l_, l_.c.league_id == c_.c.league_id) \
             .join(jtl_, jtl_.c.jewel_type_id == j_.c.jewel_type_id) \
             .join(gl_, gl_.c.general_id == j_.c.general_id) \
             .group_by(jtl_.c.type_name, gl_.c.general_name, gl_.c.keystone_name, l_.c.league_name, l_.c.league_id)

    totals_query = select(func.count().label('total'),
                          literal("ALL").label('type_name'),
                          literal("ALL").label('general_name'),
                          literal("ALL").label('keystone_name'),
                          l_.c.league_name.label('league_name'),
                          l_.c.league_id.label('league_id'),
                          l_.c.hardcore.label('hardcore')) \
            .join_from(j_, c_, j_.c.character_id == c_.c.character_id) \
            .join(l_, l_.c.league_id == c_.c.league_id) \
            .group_by(l_.c.league_name, l_.c.hardcore, l_.c.league_id)

    query =  (counts_query.union_all(totals_query)
              .order_by(l_.c.league_id.desc(), literal_column('total').desc()))
    # logger.debug(query)
    return query

def execute_query_histogram_data():
    q = query_histogram_data()
    with get_engine().connect() as conn:
        results = conn.execute(q)
        return results

def format_histogram_results(query_results: List[Row]):
    """
    output: {
        'Doryani': {
            'keystone_name': 'Corrupted Soul'
            'hardcore': [
                {
                    'league_name': 'Hardcore Mirage',
                    'total': 123,
                    'league_id': 8
                }...
            ],
            'softcore': [
            ]
        }
    }
    """
    output = {}



    for row in query_results.mappings():
        dict_row = copy.deepcopy(dict(row))
        # logger.debug(dict_row)
        general_name = dict_row['general_name']
        if output.get(general_name) is None:
            output[general_name] = {
                'keystone_name': dict_row['keystone_name'],
                'jewel_type': dict_row['type_name'],
                'hardcore': [],
                'softcore': []
            }

        hardcore_label = 'hardcore' if dict_row['hardcore'] is True else 'softcore'
        output[general_name][hardcore_label].append({
            # 'jewel_type': dict_row['type_name'],
            'league_name': dict_row['league_name'],
            'total': dict_row['total'],
            'league_id': dict_row['league_id']
        })

    return output


def query_class_affinities(top_k: int):
    """
    Returns a ranking of each keystone used by every ascendancy.
    Interesting to see how many inquisitors still go Corrupted Soul, or how many occultists go Dominus
    """

    counts = (
        select(
            func.count().label("total"),
            cl_.c.class_id,
            cl_.c.ascendancy_class_name,
            cl_.c.base_class_name,
            gl_.c.general_name,
            gl_.c.keystone_name,
            # j_.c.socket_id,
        )
        .select_from(
            j_
            .join(c_, c_.c.character_id == j_.c.character_id)
            .join(cl_, c_.c.class_id == cl_.c.class_id)
            .join(gl_, j_.c.general_id == gl_.c.general_id)
        )
        .group_by(
            cl_.c.class_id,
            cl_.c.ascendancy_class_name,
            gl_.c.general_name,
            gl_.c.keystone_name,
            # j_.c.socket_id,
        )
        .cte("counts")
    )

    ranked = (
        select(
            counts,
            func.row_number()
            .over(
                partition_by=counts.c.ascendancy_class_name,
                order_by=counts.c.total.desc(),
            )
            .label("rn"),
        )
        .cte("ranked")
    )

    query = (
        select(
            ranked.c.total,
            ranked.c.class_id,
            ranked.c.ascendancy_class_name,
            ranked.c.base_class_name,
            ranked.c.general_name,
            ranked.c.keystone_name,
            # ranked.c.socket_id,
        )
        .where(ranked.c.rn <= top_k)
        .order_by(
            ranked.c.ascendancy_class_name,
            ranked.c.rn,
        )
    )

    return query

def execute_query_class_affinities(top_k: int):
    q = query_class_affinities(top_k)
    with get_engine().connect() as conn:
        results = conn.execute(q)
        return results

def format_class_affinities_results(query_results: List[Row]):
    """
    {
        "Ascendant": [
            {
                'total': 123,
                'general_name': 'Caspiro',
                'keystone_name': 'Supreme Ostentation'
            }
        ]
    }
    """

    output = {}

    for row in query_results.mappings():
        formatted_row = copy.deepcopy(dict(row))
        class_name = formatted_row['ascendancy_class_name']
        if output.get(class_name) is None:
            output[class_name] = {}
            output[class_name]['base_class'] = formatted_row['base_class_name']
            output[class_name]['class_id'] = formatted_row['class_id']
            output[class_name]['counts'] = []

        formatted_row.pop('class_id')
        formatted_row.pop('base_class_name')
        formatted_row.pop('ascendancy_class_name')
        output[class_name]['counts'].append(formatted_row)

    return output

