import logging
from app.db import get_engine
from app.models import c_, l_, j_, jtl_, gl_, mml_, cl_, sl_, v_
from sqlalchemy.sql import select, func, distinct, alias, table, column
from sqlalchemy import text, cast, literal_column, and_, tuple_
from sqlalchemy.dialects.postgresql import INTEGER, TEXT
from sqlalchemy.sql.expression import lateral, true, null
from sqlalchemy.orm import aliased
from sqlalchemy.engine import Row
from app.views.view_helpers.view_search_helpers import query_jewel_search, SearchRequest, mml1, mml2


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
