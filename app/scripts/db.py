from datetime import datetime
from dataclasses import dataclass
from typing import List, Tuple
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import select, update, func

from app.app_config import get_config
from app.db import get_engine
from app.models import c_, l_, j_, jtl_, gl_
from app.util.parse_jewel import ParsedJewel, parse_jewel_mods, mf_mod_int_to_strs, mf_mod_strs_to_int
from app.util.lut_cache import LutData
from app.scripts.classes import Jewel
from app.singletons import LD_CACHE


@dataclass
class League:
    league_id: int
    league_name: str
    hardcore: bool
    league_start: str
    league_end: str

def get_leagues() -> List[League]:
    """
    Get the current leagues we want to poll. For now this is Softcore and Hardcore trade leagues.
    """

    with get_engine().connect() as conn:
        q = select(l_.c.league_id,
                   l_.c.league_name,
                   l_.c.hardcore,
                   l_.c.league_start,
                   l_.c.league_end).where(l_.c.league_name.in_(get_config().LIVE_LEAGUES))
        leagues = conn.execute(q).fetchall()
        return leagues

@dataclass
class Character:
    league_id: int
    ggg_id: str
    character_name: str
    class_id: int
    character_level: int
    account_name: str
    ladder_rank: int
    delve_depth: int

def add_character(character: Character) -> Tuple[int, bool]:
    """ Upsert the given character, returning the new or affected character_id. """
    with get_engine().connect() as conn:
        upsert = insert(c_).returning(c_.c.character_id, c_.c.timeout_counter).values(
            league_id=character.league_id,
            ggg_id=character.ggg_id,
            character_name=character.character_name,
            class_id=character.class_id,
            character_level=character.character_level,
            account_name=character.account_name,
            ladder_rank=character.ladder_rank,
            delve_depth=character.delve_depth,
            last_scan=datetime.now().isoformat()
        )
        upsert = upsert.on_conflict_do_update(constraint='uk_character_ggg_id',
                                              set_={'ladder_rank': character.ladder_rank,
                                                    'class_id': character.class_id,
                                                    'character_level': character.character_level,
                                                    'delve_depth': character.delve_depth,
                                                    'last_scan': datetime.now().isoformat()})
        results = conn.execute(upsert).first()._asdict()
        conn.commit()
        return results['character_id'], results['timeout_counter']

def add_or_update_character_from_ladder_entry(ladder_entry: dict) -> Tuple[int, bool]:
    character = Character(ladder_entry['league_id'],
                             ladder_entry['character']['id'],
                             ladder_entry['character']['name'],
                             LD_CACHE.class_ids[ladder_entry['character']['class']],
                             ladder_entry['character']['level'],
                             ladder_entry['account']['name'],
                             ladder_entry['rank'],
                             ladder_entry['character'].get('depth', {}).get('default', 0))

    return add_character(character)

def decrement_character_timeout(character_id: int, timeout_counter: int):
    with get_engine().connect() as conn:
        up = update(c_).where(c_.c.character_id == character_id).values(timeout_counter=timeout_counter - 1)
        conn.execute(up)
        conn.commit()

def send_character_to_timeout(character_id: int) -> int:
    with get_engine().connect() as conn:
        up = update(c_).returning(c_.c.next_timeout_max) \
            .where(c_.c.character_id == character_id) \
            .values(next_timeout_max=func.least(c_.c.next_timeout_max * 2, get_config().MAX_CHARACTER_TIMEOUT),
                    timeout_counter=c_.c.next_timeout_max)
        results = conn.execute(up).scalar()
        conn.commit()
        return results

def reset_timeout_max(character_id: int):
    with get_engine().connect() as conn:
        up = update(c_).where(c_.c.character_id == character_id) \
            .values(next_timeout_max=1)
        conn.execute(up)
        conn.commit()

def get_character_jewel(character_id: int) -> Jewel:
    with get_engine().connect() as conn:
        results = conn.execute(select(j_.c.jewel_id,
                                      j_.c.character_id,
                                      jtl_.c.type_name.label('jewel_type'),
                                      j_.c.seed,
                                      gl_.c.general_name.label('general'),
                                      j_.c.mf_mods,
                                      j_.c.drawing,
                                      j_.c.socket_index)
                               .join(jtl_, jtl_.c.jewel_type_id == j_.c.jewel_type_id)
                               .join(gl_, gl_.c.general_id == j_.c.general_id)
                               .where(j_.c.character_id == character_id)
                               .order_by(j_.c.scan_date.desc())).first()

        if results is None:
            return None
        else:
            results = results._asdict()
            if results['mf_mods'] is not None:
                mf_strings = mf_mod_int_to_strs(results['mf_mods'], LD_CACHE.mf_mod_map)
            else:
                mf_strings = []
            return Jewel(jewel_id=results['jewel_id'],
                         character_id=results['character_id'],
                         jewel_type=results['jewel_type'],
                         seed=results['seed'],
                         general=results['general'],
                         mf_mods=mf_strings,
                         drawing=results['drawing'],
                         socket_id=results['socket_id'])

def add_jewel(jewel: ParsedJewel, drawing_dict: dict,  character_id: int):

    mf_mods = None
    if jewel.mf_mods:
        mf_mods = mf_mod_strs_to_int(jewel.mf_mods, LD_CACHE.mf_mod_map)
    with get_engine().connect() as conn:
        conn.execute(insert(j_).values(character_id=character_id,
                                       jewel_type_id=LD_CACHE.jewel_type_ids[jewel.jewel_type],
                                       seed=jewel.seed,
                                       general_id=LD_CACHE.general_list[jewel.general],
                                       mf_mods=mf_mods,
                                       socket_id=jewel.socket_index,
                                       drawing=drawing_dict,
                                       initial_scan_date=datetime.now().isoformat(),
                                       scan_date=datetime.now().isoformat()))
        conn.commit()

def update_jewel_scan_date_and_drawing(jewel_id: int, jewel_drawing: dict):
    with get_engine().connect() as conn:
        conn.execute(update(j_).where(j_.c.jewel_id == jewel_id).values(scan_date=datetime.now().isoformat(), drawing=jewel_drawing))
        conn.commit()
