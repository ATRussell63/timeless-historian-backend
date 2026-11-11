import logging
from math import ceil
from typing import List, Dict
from itertools import zip_longest

from app.scripts import db
from app.app_config import get_config
from app.scripts.poll_character import process_single_character
from app.util.gggapi import GGGApi

logger = logging.getLogger('main')

API = GGGApi()

def poll_ladder():
    leagues = db.get_leagues()
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
            account_name = entry['account']['name']
            character_name = entry['character']['name']
            ggg_id = entry['character']['id']
            ascendancy_name = entry['character']['class']
            logger.debug(f'Processing entry for {character_name} - {account_name} - {ggg_id}...')

            character_id, timeout_counter = db.add_or_update_character_from_ladder_entry(entry)
            # if character is in timeout just decrement and bail
            if timeout_counter > 0:
                logger.debug(f"Character's timeout is {timeout_counter} . Decrementing and moving on...")
                db.decrement_character_timeout(character_id, timeout_counter)
            else:
                process_single_character(character_id, account_name, character_name, ggg_id, ascendancy_name)

            logger.debug(f'Finished processing {character_name} - {account_name} - {ggg_id}')
            counter += 1
        except Exception as e:
            logger.error(f'Failed process_single_ladder_entry: {e}')

def filter_ladder_entries(entries: List[Dict]) -> List[Dict]:
    # ascended, leveled, public and alive
    def filter_conditions(entry):
        return entry.get('character', {}).get('class', '') in db.LD_CACHE.class_ids \
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

def get_league_ladder(league_name: str) -> List[dict]:

    limit_max = min(get_config().LADDER_MAX, 200)
    ladder_chunks = ceil(get_config().LADDER_MAX / limit_max)
    ladder_entries = []

    for x in range(ladder_chunks):
        try:
            response_body = API.get_ladder_chunk(league_name, limit_max, x).json()
        except Exception as e:
            response_body = {}
            logger.error(f'Something went wrong while getting chunk {x} for league {league_name}! Error: {e}')
        ladder_entries += response_body.get('entries', [])

    return ladder_entries