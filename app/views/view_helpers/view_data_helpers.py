import logging
from app.db import get_engine
from app.models import c_, l_, j_, jtl_, gl_, mml_, cl_, sl_, v_
from sqlalchemy.sql import select, func, distinct, alias, table, column
from sqlalchemy import text, cast, literal_column, and_, tuple_
from sqlalchemy.dialects.postgresql import INTEGER, TEXT
from sqlalchemy.sql.expression import lateral, true, null
from sqlalchemy.orm import aliased
from sqlalchemy.engine import Row


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
