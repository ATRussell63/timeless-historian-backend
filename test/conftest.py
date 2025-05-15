import logging
import pytest
from app.db import get_engine
from app.models import c_, j_, l_
from sqlalchemy import delete
from sqlalchemy.sql import Delete

logger = logging.getLogger('main')


@pytest.fixture(autouse=True)
def test_config():
    from app.app_config import create_config
    config = create_config('test/test_config.ini')
    yield config


@pytest.fixture()
def db_engine(test_config):
    yield get_engine()


def delete_jewels() -> Delete:
    return delete(j_).where(j_.c.jewel_id >= '0')


def delete_characters() -> Delete:
    return delete(c_).where(c_.c.character_id >= '0')


def delete_leagues() -> Delete:
    return delete(l_).where(l_.c.league_id >= '0')


@pytest.fixture()
def clean_tables(db_engine):
    with db_engine.connect() as conn:
        dj = delete_jewels()
        dc = delete_characters()
        dl = delete_leagues()

        logger.debug('Deleting jewel table...')
        dj_result = conn.execute(dj)
        logger.debug(f'Deleted {dj_result.rowcount} entries from `jewel`')

        logger.debug('Deleting character table...')
        dc_result = conn.execute(dc)
        logger.debug(f'Deleted {dc_result.rowcount} entries from `character`')

        logger.debug('Deleting league table...')
        dl_result = conn.execute(dl)
        logger.debug(f'Deleted {dl_result.rowcount} entries from `league`')

        conn.commit()
