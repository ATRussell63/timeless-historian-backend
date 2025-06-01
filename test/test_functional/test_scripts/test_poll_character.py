import pytest
from sqlalchemy.sql import select

from app.models import c_, j_, l_
from app.scripts import poll_character as pc
from app.scripts.poll_character import League

SETTLERS_RANK_ONE = {
    "rank": 1,
    "dead": False,
    "public": True,
    "character": {
        "id": "8674d2e0a0d350b81287999529cb79b0b0007059083a65610bcb128362c5a863",
        "name": "CHUCHU_STAINING",
        "level": 100,
        "class": "Ascendant",
        "experience": 4250334444
    },
    "account": {
        "name": "cutiechuchu#6132",
        "challenges": {
            "set": "Village",
            "completed": 6,
            "max": 40
        },
        "twitch": {
            "name": "chuchupoe"
        }
    }
}

DIVAYTH_FYR = {
    "rank": 9001,
    "dead": False,
    "public": True,
    "character": {
        "id": "8674d2e0a0d350b81287999529cb79b0b0007059083a65610bcb128362c5a863",
        "name": "DIVAYTH_FYR",
        "level": 100,
        "class": "Hierophant",
        "experience": 4250334444
    },
    "account": {
        "name": "Rooballeux#6674",
        "challenges": {
            "set": "Village",
            "completed": 6,
            "max": 40
        },
    }
}

STEVE = {
    "rank": 3,
    "dead": False,
    "public": True,
    "character": {
        "id": "24a852d3c4e0f6dad8edfa63f947a9e72aa9d3d7bc7268450fad844fb2cbaf8c",
        "name": "NeedForSteveUnderground",
        "level": 100,
        "class": "Juggernaut",
        "experience": 4250334444,
        "depth": {
            "default": 58568,
            "solo": 58568
        }
    },
    "account": {
        "name": "turdtwisterx#4882",
        "challenges": {
            "set": "Village",
            "completed": 23,
            "max": 40
        },
        "twitch": {
            "name": "turdtwisterx"
        }
    }
}


# @pytest.fixture()
# def add_settlers_league():
#     settlers = League(name='Settlers',
#                       hardcore=False,
#                       league_start='2024-07-26 18:00:00+00:00',
#                       league_end=None)
#     yield pc.add_league(settlers)


@pytest.fixture
def get_settlers_id(test_config, db_engine):
    with db_engine.connect() as conn:
        q = select(l_.c.league_id).select_from(l_).where(l_.c.league_name == 'Settlers')
        league_id = conn.execute(q).scalar()
        yield league_id


def test_get_league_ladder(test_config):
    ladder_entries = pc.get_league_ladder('Settlers')

    assert len(ladder_entries) == test_config.LADDER_MAX

    assert ladder_entries[0] == SETTLERS_RANK_ONE


def test_process_single_ladder_entry(test_config, db_engine, clean_tables, get_settlers_id):
    settlers_id = get_settlers_id
    DIVAYTH_FYR['league_id'] = settlers_id
    pc.process_single_ladder_entry(DIVAYTH_FYR)

    with db_engine.connect() as conn:
        characters = conn.execute(select(c_)).fetchall()
        jewels = conn.execute(select(j_)).fetchall()

        assert len(characters) == 1
        assert len(jewels) == 1

        c = characters[0]
        j = jewels[0]

        assert c.league_id == settlers_id
        assert c.character_name == 'DIVAYTH_FYR'
        assert c.class_id == 19
        assert c.character_level == 100
        assert c.account_name == 'Rooballeux#6674'
        assert c.ladder_rank == 9001

        assert j.character_id == c.character_id
        assert j.jewel_type_id == 1
        assert j.seed == 7875
        assert j.general_id == 14
        assert j.mf_mods == 4608
        assert j.socket_id == 6


def test_process_divayth_isolated(test_config, db_engine, delete_divayth_fyr, get_settlers_id):
    settlers_id = get_settlers_id
    DIVAYTH_FYR['league_id'] = settlers_id
    pc.process_single_ladder_entry(DIVAYTH_FYR, settlers_id)


# def test_process_steve_isolated(test_config, db_engine, delete_steve):
#     settlers_id = 19
#     pc.process_single_ladder_entry(STEVE, settlers_id)
#     This test is enshrined in memory of NeedForSteveUnderground
#     Who valiantly fell in battle against the forces of darkness in a voided Valdo map


def test_process_mutiple_ladder_entries(test_config, db_engine, clean_tables):
    pc.poll_ladder()

    with db_engine.connect() as conn:
        characters = conn.execute(select(c_)).fetchall()
        assert len(characters) == test_config.MAX_PROCESSED_CHARACTERS


def test_poll_ladder_persistent(test_config, db_engine):
    pc.poll_ladder()


def test_poll_character_times_out_character_on_subsequent_runs(test_config, db_engine, clean_tables, get_settlers_id):
    settlers_id = get_settlers_id
    DIVAYTH_FYR['league_id'] = settlers_id
    pc.process_single_ladder_entry(DIVAYTH_FYR)
    pc.process_single_ladder_entry(DIVAYTH_FYR)

    with db_engine.connect() as conn:
        characters = conn.execute(select(c_)).fetchall()
        c = characters[0]

        assert c.timeout_counter == 1
        assert c.next_timeout_max == 2


def test_poll_character_decrements_timeout(test_config, db_engine, clean_tables, get_settlers_id):
    settlers_id = get_settlers_id
    DIVAYTH_FYR['league_id'] = settlers_id
    pc.process_single_ladder_entry(DIVAYTH_FYR)
    pc.process_single_ladder_entry(DIVAYTH_FYR)
    pc.process_single_ladder_entry(DIVAYTH_FYR)

    with db_engine.connect() as conn:
        characters = conn.execute(select(c_)).fetchall()
        c = characters[0]

        assert c.timeout_counter == 0
        assert c.next_timeout_max == 2


def test_poll_character_doubles_timeout_on_repeat_offense(test_config, db_engine, clean_tables, get_settlers_id):
    settlers_id = get_settlers_id
    DIVAYTH_FYR['league_id'] = settlers_id
    pc.process_single_ladder_entry(DIVAYTH_FYR)
    pc.process_single_ladder_entry(DIVAYTH_FYR)
    pc.process_single_ladder_entry(DIVAYTH_FYR)
    pc.process_single_ladder_entry(DIVAYTH_FYR)

    with db_engine.connect() as conn:
        characters = conn.execute(select(c_)).fetchall()
        c = characters[0]

        assert c.timeout_counter == 2
        assert c.next_timeout_max == 4
