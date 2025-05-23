from sqlalchemy.engine import create_engine, URL, Engine, Row
from sqlalchemy.pool import QueuePool
from typing import List, Dict

from app.app_config import get_config

_db_engine = None


def get_engine() -> Engine:
    global _db_engine

    if not _db_engine:
        _db_engine = init_engine()

    return _db_engine


def init_engine() -> Engine:
    config = get_config()
    conn_args = {
        'host': config.DATABASE_HOST,
        'port': config.DATABASE_PORT,
        'username': config.DATABASE_USER,
        'password': config.DATABASE_PASSWORD,
        'database': config.DATABASE_NAME
    }

    conn_url = URL.create('postgresql', **conn_args)
    engine = create_engine(conn_url,
                           future=True,
                           poolclass=QueuePool,
                           pool_size=3,
                           max_overflow=-1,
                           pool_pre_ping=True,
                           echo=config.SQLALCHEMY_ECHO)
    return engine


def dict_results(results: List[Row]) -> List[Dict]:
    """Return result rows as dicts"""
    return [row._asdict() for row in results]