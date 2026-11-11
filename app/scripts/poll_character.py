import logging
import re
from typing import Optional, List

from app.scripts import db
from app.scripts.classes import Jewel, DrawingRoot
from app.scripts.apply_jewel_effects import apply_timeless_jewel_effects, apply_abyss_domain_jewel_effects, \
    apply_zorath_effects
from app.scripts.drawing.ascend_tree_drawing import ZORATH_UNSUPPORTED_CLASSES, make_zorath_drawing
from app.scripts.drawing.cutout_by_socket import make_timeless_cutout_for_socket, make_abyss_cutout
from app.scripts.minify_drawing import convert_drawing_to_minified_json
from app.scripts.poll_ladder import API

from app.util.parse_jewel import ParsedJewel, parse_jewel_mods
from app.util.gggapi import APIJewel
from app.util.exceptions import PrivateAccountException, UselessJewelException, NoJewelEquippedException, \
    AnointRetrievalException, PassiveSkillsRetrievalException

logger = logging.getLogger('main')

def process_single_character(character_id, account_name, character_name, ggg_id, ascendancy_name):

    try:
        logger.debug(f'Starting API calls for {character_name} - {account_name} - {ggg_id}')
        # all necessary API calls to prepare for making the jewel drawing
        passive_skills_response = get_character_passive_tree_and_items(account_name, character_name)

        if passive_skills_response is None:
            logger.error("Error retrieving character info, response is empty")
            logger.debug(f'Finished processing {character_name} - {account_name} - {ggg_id}')
            return

        hashes, equipped_jewels = API.parse_get_passives_response(passive_skills_response)
        jewel = get_equipped_timeless_jewel(equipped_jewels)
        check_does_jewel_work(jewel, ascendancy_name)

        # get the name of the Forbidden Flesh & Flame 'anointed' ascend node
        ff_ascend_node = get_flesh_and_flame_ascendancy_node(equipped_jewels)

        # get the names of the anointed passives (not included in the normal hash list)
        items_response = API.get_equipped_items(account_name, character_name)
        anointed_nodes = get_anointed_node_names(items_response.json())

        logger.debug(f'Retrieved all data necessary to process jewel for {character_name} - {account_name} - {ggg_id}')
    except PassiveSkillsRetrievalException:
        logger.error(f'Encountered an error while trying to retrieve passive-skills')
        return
    except PrivateAccountException:
        logger.error(f'This account was identified as private. \
                       Account Name: {account_name} - Character: {character_name}')
        db.send_character_to_timeout(character_id)
        return
    except UselessJewelException:
        logger.debug(f'This character has a Zorath jewel equipped on an ascendancy where it does not grant a keystone. \
                             Account Name: {account_name} - Character: {character_name}')
        logger.debug('Sending them to prison and may god have mercy on their soul')
        db.send_character_to_timeout(character_id)
        return
    except NoJewelEquippedException:
        logger.debug(f'Character {character_name} was not wearing a timeless jewel, sending them to time out.')
        db.send_character_to_timeout(character_id)
        return
    except AnointRetrievalException as e:
        logger.error(f"Failed to retrieve equipped items (to parse anoints): {e}")
        return

    # we have all the data we need, time to make the jewel drawing
    try:
        base_class_name = db.LD_CACHE.base_classes[ascendancy_name]
        jewel_dict = generate_jewel_drawing(jewel, hashes, anointed_nodes,
                                            base_class_name, ascendancy_name, ff_ascend_node)
    except Exception as e:
        logger.error(f'Error processing drawing for jewel: {e}')
        jewel_dict = {
            'error': str(e)
        }

    # is equipped jewel the same that's already in the db?
    db_jewel = db.get_character_jewel(character_id)

    # if they are using the same ITEM (type, general, seed, mf_mods) and in the same slot
    if db_jewel_matches_equipped(db_jewel, jewel):
        # update the drawing but put them in timeout
        logger.debug(f"Character {character_name}'s jewel is the same item as before, in the same socket.")
        db.update_jewel_scan_date_and_drawing(db_jewel.jewel_id, jewel_dict)
        timeout = db.send_character_to_timeout(character_id)
        logger.debug(f'Sending them to time out for {timeout} runs.')
    else:
        # add new jewel
        db.add_jewel(jewel, jewel_dict, character_id)
        db.reset_timeout_max(character_id)

def get_anointed_node_names(items_response_body: dict) -> List[str]:
    try :
        anointed_notables = []
        for item in items_response_body['items']:
            enchant_mods = item.get('enchantMods', [])
            for mod in enchant_mods:
                if 'Allocates' not in mod:
                    continue
                else:
                    anointed_notables.append(mod.split('Allocates ')[1])

        return anointed_notables
    except Exception as e:
        raise AnointRetrievalException(e)

def get_character_passive_tree_and_items(account_name: str, character_name: str) -> Optional[dict]:
    response = API.get_passive_skills(account_name, character_name)
    response_body = response.json()

    if response_body is None:
        logger.error(f'passive-skills response status was {response.status_code}')
        raise PassiveSkillsRetrievalException()

    return response_body

def get_equipped_timeless_jewel(equipped_jewels: List[APIJewel]) -> ParsedJewel:
    for jewel in equipped_jewels:
        if jewel.typeLine.upper() == 'TIMELESS JEWEL' \
            or jewel.name in db.LD_CACHE.abyss_domain_list \
            or jewel.name == 'Reclaimed Malevolence':
            return parse_jewel_mods(jewel, db.LD_CACHE)

    raise NoJewelEquippedException()

def check_does_jewel_work(jewel: ParsedJewel, ascendancy_name: str):
    if jewel.jewel_type is 'Reclaimed Malevolence' \
            and ascendancy_name.upper() in ZORATH_UNSUPPORTED_CLASSES:
        raise UselessJewelException()

def db_jewel_matches_equipped(db_jewel: Jewel, equipped_jewel: ParsedJewel) -> bool:
    if not db_jewel or not equipped_jewel:
        return False

    else:
        return db_jewel.jewel_type == equipped_jewel.jewel_type and \
            int(db_jewel.seed) == int(equipped_jewel.seed) and \
            db_jewel.general == equipped_jewel.general and \
            int(db_jewel.socket_id) == int(equipped_jewel.socket_index or 0) and \
            set(db_jewel.mf_mods) == set(equipped_jewel.mf_mods)
        # TODO - can I get rid of this comment?
        # set(db_jewel.drawing['jewel_stats']) == set(dataclasses.asdict(equipped_jewel.drawing)['jewel_stats'])
        # jewel stats matching is a weak implication that the allocated passives didn't change
        # I can't compare the whole drawing because sub lists are unhashable to set

def get_flesh_and_flame_ascendancy_node(equipped_jewels: List[APIJewel]) -> Optional[str]:
    """ Since Zorath exists now, we care about any 'anointed' ascendancy notables. """
    flame_name = ""
    flesh_name = ""

    pattern = r'Allocates (.*) if'

    for jewel in equipped_jewels:
        desc_line = jewel.explicitMods[0].get('description')

        if jewel.name == 'Forbidden Flesh':
            flesh_name = re.search(pattern, desc_line).group(1)
        elif jewel.name == 'Forbidden Flame':
            flame_name = re.search(pattern, desc_line).group(1)

    if flesh_name == flame_name:
        return flesh_name
    else:
        return None

def generate_jewel_drawing(jewel: ParsedJewel, hashes: List[int], anointed_node_names: List[str],
                           base_class: str, ascendancy: str, ff_ascend_node: Optional[str]) -> dict:

    drawing: DrawingRoot
    if jewel.jewel_type in db.LD_CACHE.abyss_domain_list:
        drawing = make_abyss_cutout()
        drawing = apply_abyss_domain_jewel_effects(drawing)
    elif jewel.jewel_type is 'Reclaimed Malevolence':
        drawing = make_zorath_drawing()
        drawing = apply_zorath_effects(drawing)
    else:
        drawing = make_timeless_cutout_for_socket(jewel=jewel,
                                                  allocated_hashes=hashes,
                                                  anointed_node_names=anointed_node_names)
        drawing = apply_timeless_jewel_effects(jewel, drawing)

    return convert_drawing_to_minified_json(drawing)
