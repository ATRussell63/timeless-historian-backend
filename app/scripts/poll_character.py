import dataclasses
import logging
from math import ceil
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict
from app.app_config import get_config
from app.db import get_engine
from app.models import c_, l_, j_, jtl_, gl_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import select, update

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
    name: str
    hardcore: bool
    league_start: str
    league_end: str


def get_leagues() -> List[League]:
    """
    Get the current leagues we want to poll. For now this is Softcore and Hardcore trade leagues.
    """

    # TODO fix the league endpoint stuff after we get real api access
    poll_leagues = [League(name='Settlers',
                           hardcore=False,
                           league_start='2024-07-26 18:00:00+00:00',
                           league_end=None),
                    League(name='Hardcore Settlers',
                           hardcore=True,
                           league_start='2024-07-26 18:00:00+00:00',
                           league_end=None)]

    # api = GGG_Api()
    # response = api.get_leagues()

    # poll_leagues = []
    # for league in response.json():
    #     if league['category']['current'] is True and league['realm'] == 'pc':
    #         ssf = False
    #         hardcore = False
    #         for league_rule in league['rules']:
    #             if league_rule['id'] == 'NoParties':
    #                 ssf = True
    #             if league_rule['id'] == 'Hardcore':
    #                 hardcore = True

    #         if ssf:
    #             continue

    #         poll_leagues.append(League(name=league['id'],
    #                                    hardcore=hardcore,
    #                                    league_start=league['startAt'],
    #                                    league_end=league['endAt']))

    return poll_leagues


def add_league(league: League) -> int:
    """ Upsert the given league, only updating the end date if we have a new value. """
    with get_engine().connect() as conn:
        upsert = insert(l_).returning(l_.c.league_id).values(
            league_name=league.name,
            hardcore=league.hardcore,
            league_start=league.league_start,
            league_end=league.league_end
        )
        upsert = upsert.on_conflict_do_update(
            constraint='uk_league_name', set_={'league_end': league.league_end}
        )
        print(upsert)
        result = conn.execute(upsert).first()
        conn.commit()
        return result['league_id']


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


def add_character(character: Character) -> int:
    """ Upsert the given character, returning the new or affected character_id. """
    with get_engine().connect() as conn:
        upsert = insert(c_).returning(c_.c.character_id).values(
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
        character_id = conn.execute(upsert).scalar()
        conn.commit()
        return character_id


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
            set(db_jewel.mf_mods) == set(equipped_jewel.mf_mods) and \
            set(db_jewel.drawing['jewel_stats']) == set(dataclasses.asdict(equipped_jewel.drawing)['jewel_stats'])
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


def update_jewel_scan_date(jewel_id: int):
    with get_engine().connect() as conn:
        conn.execute(update(j_).where(j_.c.jewel_id == jewel_id).values(scan_date=datetime.now().isoformat()))
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


def process_single_ladder_entry(ladder_entry: dict, league_id: int):
    api = GGG_Api()
    account_name = ladder_entry['account']['name']
    character_name = ladder_entry['character']['name']

    logger.debug(f'Processing entry for {character_name} - {account_name}...')

    try:
        response = api.get_passive_skills(account_name, character_name)
    except PrivateAccountException:
        logger.error(f'This account was identified as private. \
                       Account Name: {account_name} - Character: {character_name}')
        # logger.error(f'Full error: {e}')
        return

    # is the character wearing a timeless jewel?
    parsed_jewel = get_equipped_timeless_jewel_obj(response.json())

    if parsed_jewel is None:
        logger.debug(f'Character {character_name} was not wearing a timeless jewel.')
        return

    # convert jewel to dict
    parsed_jewel.drawing = dataclasses.asdict(parsed_jewel.drawing)
    # trim down jewel data
    #  - this is a pretty damn stupid step but I want to see how much I can shrink the response size

    def cull_edges(drawing):
        for edge in drawing['edges']:
            if edge['edge_type'] == 'CurvedEdge':
                edge.pop('absolute_center')
                edge.pop('arc_len')
            else:
                edge['ends'][0].pop('absolute')
                edge['ends'][1].pop('absolute')
        
        return drawing

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
    
    parsed_jewel.drawing = cull_edges(parsed_jewel.drawing)
    parsed_jewel.drawing = cull_nodes(parsed_jewel.drawing)

    character = Character(league_id,
                          ladder_entry['character']['id'],
                          ladder_entry['character']['name'],
                          LD_CACHE.class_ids[ladder_entry['character']['class']],
                          ladder_entry['character']['level'],
                          ladder_entry['account']['name'],
                          ladder_entry['rank'],
                          ladder_entry['character'].get('depth', {}).get('default', 0))

    # TODO - am i supposed to be doing this every time?
    character_id = add_character(character)

    # is equipped jewel the same that's already in the db?
    db_jewel = get_character_jewel(character_id)
    if db_jewel_matches_equipped(db_jewel, parsed_jewel):
        # just mark as scanned
        update_jewel_scan_date(db_jewel.jewel_id)
    else:
        # add new jewel
        add_jewel(parsed_jewel, character_id)


def poll_ladder():

    leagues = get_leagues()

    for league in leagues:
        # insert league if not already in db
        league_id = add_league(league)
        ladder_entries = get_league_ladder(league.name)

        for entry in ladder_entries:
            try:
                if entry.get('public') is True:
                    process_single_ladder_entry(entry, league_id)
            except Exception as e:
                logger.error(f'Failed process_single_ladder_entry: {e}')
