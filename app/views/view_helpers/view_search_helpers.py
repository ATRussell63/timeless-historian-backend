from dataclasses import dataclass
from flask import Request
from typing import List
import copy
from sqlalchemy.engine import Row
import logging
from app.db import get_engine
from app.models import c_, l_, j_, jtl_, gl_, mml_, cl_, sl_, v_
from sqlalchemy.sql import select, func, distinct, alias, table, column
from sqlalchemy import text, cast, literal_column, and_
from sqlalchemy.dialects.postgresql import INTEGER, TEXT
from sqlalchemy.sql.expression import lateral, true, null
from sqlalchemy.orm import aliased

logger = logging.getLogger('main')

# only declared out here because of my broke ass test endpoint
mml1 = mml_.alias('mml1')
mml2 = mml_.alias('mml2')


@dataclass
class SearchRequest:
    jewel_type: str
    seed: int
    general: str
    mf_mods: List[str]


def parse_jewel_search_request(request: Request):
    try:
        request_body = request.json
        search_data = SearchRequest(
            jewel_type=request_body['jewel_type'],
            seed=int(request_body['seed']),
            general=request_body['general'],
            mf_mods=request_body.get('mf_mods', [])
        )
    except KeyError as e:
        logger.error(f'Search request missing a parameter: {e}')
    
    return search_data


def query_jewel_search(search_data: SearchRequest):

    # TODO - # .distinct(c_.c.ggg_id) \
    # maybe include this again later, jewels are supposed to update scan date instead of new inserts
    # but I might change my mind later about this

    q = select(l_.c.league_name,
               l_.c.league_id,
               l_.c.hardcore,
               (func.now().between(l_.c.league_start, l_.c.league_end).label('league_active')),
               c_.c.character_name,
               c_.c.account_name,
               c_.c.ggg_id,
               c_.c.character_level,
               c_.c.ladder_rank,
               cl_.c.ascendancy_class_name.label('ascendancy_name'),
               cl_.c.base_class_name.label('base_class'),
               jtl_.c.type_name.label('jewel_type'),
               j_.c.seed,
               gl_.c.general_name.label('general'),
               j_.c.mf_mods,
               j_.c.drawing,
               j_.c.socket_id,
               sl_.c.pob_name.label('socket_name'),
               sl_.c.description.label('socket_description'),
               v_.c.nickname.label('vip'),
               j_.c.initial_scan_date,
               j_.c.scan_date,
               (func.floor(func.extract('epoch', j_.c.initial_scan_date - l_.c.league_start) / (7 * 24 * 60 * 60)) + 1).label('start_week'),
               (func.floor(func.extract('epoch', j_.c.scan_date - l_.c.league_start) / (7 * 24 * 60 * 60)) + 1).label('end_week')) \
        .join_from(j_, c_, j_.c.character_id == c_.c.character_id) \
        .join(jtl_, jtl_.c.jewel_type_id == j_.c.jewel_type_id) \
        .join(gl_, gl_.c.general_id == j_.c.general_id) \
        .join(l_, l_.c.league_id == c_.c.league_id) \
        .join(cl_, cl_.c.class_id == c_.c.class_id) \
        .join(sl_, sl_.c.socket_id == j_.c.socket_id) \
        .join(v_, v_.c.account_name == c_.c.account_name, isouter=True) \
        .where((j_.c.seed == search_data.seed) & (jtl_.c.type_name == search_data.jewel_type)) \
        .order_by(c_.c.ggg_id, j_.c.scan_date.desc(), l_.c.league_id)

    if search_data.jewel_type == 'Militant Faith':
        
        # TODO - the coalesce to 65536 is from testing, not necessary in prod
        match_count = (
            cast(func.mf_mods_contains_bit(func.coalesce(j_.c.mf_mods, 65536), func.coalesce(mml1.c.mod_bit, 0)), INTEGER)
            + cast(func.mf_mods_contains_bit(func.coalesce(j_.c.mf_mods, 65536), func.coalesce(mml2.c.mod_bit, 0)), INTEGER)
        ).label("mf_mods_match_count")

        q = q.join(mml1, true()).join(mml2, true())
        q = q.add_columns(match_count)
        q = q.add_columns(func.get_mod_text_by_idx(j_.c.mf_mods, 1).label('mf_mod_1'),
                          func.get_mod_text_by_idx(j_.c.mf_mods, 2).label('mf_mod_2'))
        q = q.where(mml1.c.mod_text == search_data.mf_mods[0])
        q = q.where(mml2.c.mod_text == search_data.mf_mods[1])

    return q


def perform_jewel_search(search_data: SearchRequest) -> List[Row]:
    """Search for any jewels that match the type and seed from search_data."""

    with get_engine().connect() as conn:
        query = query_jewel_search(search_data)
        results = conn.execute(query)
        return results


def format_jewel_search_results(search_results: List[Row], search_data: SearchRequest) -> dict:
    output = {}

    for row in search_results.mappings():
        formatted_row = copy.deepcopy(dict(row))
        
        formatted_row['general_match'] = formatted_row['general'] == search_data.general
        formatted_row['socket'] = {
            'id': formatted_row['socket_id'],
            'name': formatted_row['socket_name'],
            'description': formatted_row['socket_description']
        }
        formatted_row.pop('socket_id')
        formatted_row.pop('socket_name')
        formatted_row.pop('socket_description')

        if not output.get(row['league_name']):
            output[row['league_name']] = {
                'league_id': row['league_id'],
                'hardcore': row['hardcore'],
                'is_active': row['league_active'],
                'jewels': []
            }

        formatted_row.pop('league_id')
        formatted_row.pop('hardcore')
        formatted_row.pop('league_active')

        output[row['league_name']]['jewels'].append(formatted_row)

    return output