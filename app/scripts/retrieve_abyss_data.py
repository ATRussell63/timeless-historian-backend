import logging
import json
from datetime import datetime

from app.util.ggg_api import GGG_Api
from app.util.exceptions import PrivateAccountException
from app.app_config import get_data_path

logger = logging.getLogger('main')

api = GGG_Api()

ABYSS_JEWELS = ["Baleful Dominion", "Festering Vengeance", "Destructive Aspiration", "Extinguishing Grasp", "Reclaimed Malevolence"]

def has_abyss_equipped(response_body: dict) -> bool:
    for item in response_body['items']:
        if item['name'] in ABYSS_JEWELS:
            return True

    return False

def record_responses_to_file(ladder: dict, passives: dict, items: dict):
    # make the dir path
    char_path = "_".join([get_data_path() + '/abyss_archive/', ladder['account'], ladder['name'], datetime.now().isoformat()])

    with open(char_path + "/ladder.json", "w", encoding="utf-8") as ladder_file:
        json.dump(ladder, ladder_file)

    with open(char_path + "/passives.json", "w", encoding="utf-8") as passives_file:
        json.dump(passives, passives_file)

    with open(char_path + "/items.json", "w", encoding="utf-8") as items_file:
        json.dump(items, items_file)


def retrieve_single_abyss(ladder_entry: dict):
    account_name = ladder_entry['account']['name']
    character_name = ladder_entry['character']['name']
    ggg_id = ladder_entry['character']['id']

    logger.debug(f'Processing entry for {character_name} - {account_name} - {ggg_id}...')

    try:
        passives_response = api.get_passive_skills(account_name, character_name)

        if not has_abyss_equipped(passives_response.json()):
            logger.debug(f'This character was not wearing an abyss historic jewel')
            logger.debug(f'Finished processing {character_name} - {account_name} - {ggg_id}')
            return

        items_response = api.get_equipped_items(account_name, character_name)
        record_responses_to_file(ladder_entry, passives_response.json(), items_response.json())

    except PrivateAccountException:
        logger.error(f'This account was identified as private. \
                       Account Name: {account_name} - Character: {character_name}')
        logger.debug(f'Finished processing {character_name} - {account_name} - {ggg_id}')
        return