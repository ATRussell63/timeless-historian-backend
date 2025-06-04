import dataclasses
import logging
from math import ceil
from datetime import datetime
from dataclasses import dataclass
from itertools import zip_longest
from typing import Optional, List, Dict, Tuple
from app.app_config import get_config
from app.db import get_engine
from app.models import c_, l_, j_, jtl_, gl_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import select, update, func

from app.util.parse_jewel import ParsedJewel, parse_jewel_json_object, mf_mod_int_to_strs, mf_mod_strs_to_int
from app.util.ggg_api import GGG_Api
from app.util.exceptions import PrivateAccountException
from app.util.lut_cache import LutData
from app.scripts.jewel_radius_drawing import JewelDrawing
from app.scripts.classes import Jewel

logger = logging.getLogger('main')


def get_jewel_socket(passive_skills_response: dict):
    for jewel_socket in passive_skills_response['jewel_data']:
        if passive_skills_response['jewel_data'][jewel_socket]['type'] == 'JewelTimeless':
            return jewel_socket

    raise Exception('No timeless jewel found in jewel_data!')


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


# deprecated, will probably be manually inserting new leagues
# def add_league(league: League) -> int:
#     """ Upsert the given league, only updating the end date if we have a new value. """
#     with get_engine().connect() as conn:
#         upsert = insert(l_).returning(l_.c.league_id).values(
#             league_name=league.name,
#             hardcore=league.hardcore,
#             league_start=league.league_start,
#             league_end=league.league_end
#         )
#         upsert = upsert.on_conflict_do_update(
#             constraint='uk_league_name', set_={'league_end': league.league_end}
#         )
#         result = conn.execute(upsert).scalar()
#         conn.commit()
#         return result


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


def decrement_character_timeout(character_id: str, timeout_counter: int):
    with get_engine().connect() as conn:
        up = update(c_).where(c_.c.character_id == character_id).values(timeout_counter=timeout_counter - 1)
        conn.execute(up)
        conn.commit()


def send_character_to_timeout(character_id: str) -> int:
    with get_engine().connect() as conn:
        up = update(c_).returning(c_.c.next_timeout_max) \
            .where(c_.c.character_id == character_id) \
            .values(next_timeout_max=func.least(c_.c.next_timeout_max * 2, get_config().MAX_CHARACTER_TIMEOUT),
                    timeout_counter=c_.c.next_timeout_max)
        results = conn.execute(up).scalar()
        conn.commit()
        return results


def reset_timeout_max(character_id: str):
    with get_engine().connect() as conn:
        up = update(c_).where(c_.c.character_id == character_id) \
            .values(next_timeout_max=1)
        conn.execute(up)
        conn.commit()


LD_CACHE = LutData()


def get_character_jewel(character_id: int) -> Jewel:
    with get_engine().connect() as conn:
        results = conn.execute(select(j_.c.jewel_id,
                                      j_.c.character_id,
                                      jtl_.c.type_name.label('jewel_type'),
                                      j_.c.seed,
                                      gl_.c.general_name.label('general'),
                                      j_.c.mf_mods,
                                      j_.c.drawing,
                                      j_.c.socket_id)
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


def db_jewel_matches_equipped(db_jewel: Jewel, equipped_jewel: ParsedJewel) -> bool:
    if not db_jewel or not equipped_jewel:
        return False

    else:
        return db_jewel.jewel_type == equipped_jewel.jewel_type and \
            int(db_jewel.seed) == int(equipped_jewel.seed) and \
            db_jewel.general == equipped_jewel.general and \
            int(db_jewel.socket_id) == int(equipped_jewel.socket_id) and \
            set(db_jewel.mf_mods) == set(equipped_jewel.mf_mods)
        # set(db_jewel.drawing['jewel_stats']) == set(dataclasses.asdict(equipped_jewel.drawing)['jewel_stats'])
        # jewel stats matching is a weak implication that the allocated passives didn't change
        # I can't compare the whole drawing because sub lists are unhashable to set


def get_equipped_timeless_jewel_obj(response_body: dict) -> Optional[ParsedJewel]:
    for item in response_body['items']:
        if item['typeLine'] == 'Timeless Jewel':
            jewel = parse_jewel_json_object(item, LD_CACHE)
            # unfortunately socket is not included in the item obj so we need to do this search
            for jewel_socket in response_body['jewel_data']:
                if response_body['jewel_data'][jewel_socket]['type'] == 'JewelTimeless':
                    jewel.socket_id = jewel_socket
                    break

            try:
                jd = JewelDrawing()
                jewel.drawing = jd.make_drawing(api_response=response_body,
                                                jewel=jewel)
            except Exception as e:
                logger.error(f'Error processing drawing for jewel: {e}')
                jewel.drawing = {
                    'error': str(e)
                }
                return None
            
            return jewel

    return None


def update_jewel_scan_date_and_drawing(jewel_id: int, jewel_drawing: dict):
    with get_engine().connect() as conn:
        conn.execute(update(j_).where(j_.c.jewel_id == jewel_id).values(scan_date=datetime.now().isoformat(), drawing=jewel_drawing))
        conn.commit()


def add_jewel(jewel: Jewel, character_id: int):

    mf_mods = None
    if jewel.mf_mods:
        mf_mods = mf_mod_strs_to_int(jewel.mf_mods, LD_CACHE.mf_mod_map)
    with get_engine().connect() as conn:
        conn.execute(insert(j_).values(character_id=character_id,
                                       jewel_type_id=LD_CACHE.jewel_type_ids[jewel.jewel_type],
                                       seed=jewel.seed,
                                       general_id=LD_CACHE.general_list[jewel.general],
                                       mf_mods=mf_mods,
                                       socket_id=jewel.socket_id,
                                       drawing=jewel.drawing,
                                       initial_scan_date=datetime.now().isoformat(),
                                       scan_date=datetime.now().isoformat()))
        conn.commit()


def get_league_ladder(league_name: str) -> List[dict]:

    limit_max = min(get_config().LADDER_MAX, 200)
    ladder_chunks = ceil(get_config().LADDER_MAX / limit_max)
    ladder_entries = []

    api = GGG_Api()

    for x in range(ladder_chunks):
        try:
            response_body = api.get_ladder_chunk(league_name, limit_max, x).json()
        except Exception as e:
            response_body = {}
            logger.error(f'Something went wrong while getting chunk {x} for league {league_name}! Error: {e}')
        ladder_entries += response_body.get('entries')

    return ladder_entries


def process_single_ladder_entry(ladder_entry: dict):
    account_name = ladder_entry['account']['name']
    character_name = ladder_entry['character']['name']
    ggg_id = ladder_entry['character']['id']

    logger.debug(f'Processing entry for {character_name} - {account_name} - {ggg_id}...')

    character = Character(ladder_entry['league_id'],
                          ladder_entry['character']['id'],
                          ladder_entry['character']['name'],
                          LD_CACHE.class_ids[ladder_entry['character']['class']],
                          ladder_entry['character']['level'],
                          ladder_entry['account']['name'],
                          ladder_entry['rank'],
                          ladder_entry['character'].get('depth', {}).get('default', 0))

    character_id, timeout_counter = add_character(character)

    # if character is in timeout just decrement and bail
    if timeout_counter > 0:
        logger.debug(f"Character's timeout is {timeout_counter} . Decrementing and moving on...")
        decrement_character_timeout(character_id, timeout_counter)
        logger.debug(f'Finished processing {character_name} - {account_name} - {ggg_id}')
        return

    try:
        api = GGG_Api()
        response = api.get_passive_skills(account_name, character_name)
    except PrivateAccountException:
        logger.error(f'This account was identified as private. \
                       Account Name: {account_name} - Character: {character_name}')
        logger.debug(f'Finished processing {character_name} - {account_name} - {ggg_id}')
        return

    # is the character wearing a timeless jewel?
    parsed_jewel = get_equipped_timeless_jewel_obj(response.json())

    if parsed_jewel is None:
        logger.debug(f'Character {character_name} was not wearing a timeless jewel, sending them to time out.')
        send_character_to_timeout(character_id)
        logger.debug(f'Finished processing {character_name} - {account_name} - {ggg_id}')
        return

    # convert jewel to dict
    parsed_jewel.drawing = dataclasses.asdict(parsed_jewel.drawing)

    def cull_nodes(drawing):
        for node in drawing['nodes'].values():
            node.pop('absolute_coords')
            node.pop('group_id')
            node.pop('group_relative_coords')
            node.pop('group_absolute_coords')
            node.pop('connected_nodes')
            # jesus christ man
            node.pop('reminder')
            node.pop('orbit')
            node.pop('orbitIndex')
            node.pop('orbitRadius')
            node.pop('mods')
        
        return drawing
    
    def minimize_node_field_names(node):
        field_map = {
            'name': 'n',
            'node_id': 'i',
            'node_type': 't',
            'allocated': 'a',
            'relative_coords': 'c',
            'tooltip': 'l'
        }
        
        for k, v in field_map.items():
            node[v] = node[k]
            node.pop(k)
        return node

    def minimize_straight_edge_field_names(edge):
        # field_map = {
        #     'allocated': 'a',
        #     'ends': 'c'
        # }
        new_edge = {
            'a': edge['allocated'],
            'c': [
                {
                    'x': edge['ends'][0]['relative']['x'],
                    'y': edge['ends'][0]['relative']['y'],
                },
                {
                    'x': edge['ends'][1]['relative']['x'],
                    'y': edge['ends'][1]['relative']['y'],
                }
            ]
        }
        return new_edge

    def minimize_curved_edge_field_names(edge):
        field_map = {
            'allocated': 'a',
            'relative_center': 'c',
            'rotation': 'o',
            'radius': 'r',
            'angle': 't'
        }
        for k, v in field_map.items():
            edge[v] = edge[k]
            edge.pop(k)
        return edge

    # trim down jewel data
    parsed_jewel.drawing = cull_nodes(parsed_jewel.drawing)
    parsed_jewel.drawing.pop('jewel_coords')
    
    for node in parsed_jewel.drawing['nodes']:
        parsed_jewel.drawing['nodes'][node] = minimize_node_field_names(parsed_jewel.drawing['nodes'][node])
    
    new_straight_edges = []
    for edge in parsed_jewel.drawing['straight_edges']:
        new_straight_edges.append(minimize_straight_edge_field_names(edge))
    
    new_curved_edges = []
    for edge in parsed_jewel.drawing['curved_edges']:
        new_curved_edges.append(minimize_curved_edge_field_names(edge))
    
    parsed_jewel.drawing['straight_edges'] = new_straight_edges
    parsed_jewel.drawing['curved_edges'] = new_curved_edges

    # is equipped jewel the same that's already in the db?
    db_jewel = get_character_jewel(character_id)

    # if they are using the same ITEM (type, general, seed, mf_mods) and in the same slot
    if db_jewel_matches_equipped(db_jewel, parsed_jewel):
        # update the drawing but put them in timeout
        logger.debug(f"Character {character_name}'s jewel is the same item as before, in the same socket.")
        update_jewel_scan_date_and_drawing(db_jewel.jewel_id, parsed_jewel.drawing)
        timeout = send_character_to_timeout(character_id)
        logger.debug(f'Sending them to time out for {timeout} runs.')
    else:
        # add new jewel
        add_jewel(parsed_jewel, character_id)
        reset_timeout_max(character_id)
        logger.debug(f'Finished processing {character_name} - {account_name} - {ggg_id}')


def filter_ladder_entries(entries: List[Dict]) -> List[Dict]:
    # ascended, leveled, public and alive
    def filter_conditions(entry):
        return entry.get('character', {}).get('class', '') in LD_CACHE.class_ids \
            and entry.get('character', {}).get('level', 0) >= get_config().LEVEL_CUTOFF \
            and entry.get('public', False) is True \
            and entry.get('dead', False) is False

    return list(filter(filter_conditions, entries))


def interleave(*lists):
    return [item for group in zip_longest(*lists) for item in group if item is not None]


def apply_league_id_to_entries(entries: List[Dict], league_id: int) -> List[Dict]:
    for entry in entries:
        entry['league_id'] = league_id
    return entries


def poll_ladder():

    leagues = get_leagues()
    league_ladders = []
    for league in leagues:
        ladder_entries = get_league_ladder(league.league_name)
        ladder_entries = filter_ladder_entries(ladder_entries)
        ladder_entries = apply_league_id_to_entries(ladder_entries, league.league_id)
        league_ladders.append(ladder_entries)
    
    merged_ladder = interleave(*league_ladders)

    counter = 0
    for entry in merged_ladder:
        if counter >= get_config().MAX_PROCESSED_CHARACTERS:
            logger.debug(f'Quota of {counter} characters has been processed, quitting...')
            break

        try:
            process_single_ladder_entry(entry)
            counter += 1
        except Exception as e:
            logger.error(f'Failed process_single_ladder_entry: {e}')
