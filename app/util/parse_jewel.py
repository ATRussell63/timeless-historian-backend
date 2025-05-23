import re
from dataclasses import dataclass
from typing import Optional, List, Dict
from app.util.lut_cache import LutData


@dataclass
class ParsedJewel:
    jewel_type: str
    seed: str
    general: str
    mf_mods: List[str]
    socket_id: Optional[int] = None
    drawing: Optional[Dict] = None


def parse_jewel_raw_str(jewel_string: str, lut_data: LutData) -> ParsedJewel:
    jewel_type = parse_jewel_type(jewel_string, lut_data.jewel_type_ids)
    seed = parse_seed(jewel_string)
    general = parse_general(jewel_string, lut_data.general_list)
    mf_mods: None
    if jewel_type == 'Militant Faith':
        mf_mods = parse_militant_faith_mods(jewel_string)

    return ParsedJewel(jewel_type,
                       seed,
                       general,
                       mf_mods)


def parse_jewel_json_object(jewel_object: dict, lut_data: LutData) -> ParsedJewel:
    jewel_type_map = lut_data.jewel_type_ids
    general_map = lut_data.general_list
    jewel_type = jewel_object['name']
    assert jewel_type in jewel_type_map.keys()
    seed = re.search(r'(\d+)', jewel_object['explicitMods'][0]).group(0)
    general = re.search(r'(\w+)$', jewel_object['explicitMods'][0].split('\n')[0]).group(1)
    assert general in general_map.keys()

    mf_mods = []
    if jewel_type == 'Militant Faith':
        mf_mods = [jewel_object['explicitMods'][1], jewel_object['explicitMods'][2]]
    
    return ParsedJewel(jewel_type,
                       seed,
                       general,
                       mf_mods)


def parse_jewel_type(jewel_string: str, jewel_type_map: Dict[str, int]) -> str:
    jewel_type = re.search(r'Rarity: Unique\n(.*)', jewel_string).group(1)
    assert jewel_type in jewel_type_map.keys()
    return jewel_type


def parse_seed(jewel_string: str) -> str:
    return re.search(r'Item Level: \d\d\n(?:-*)\n\D*(\d*)', jewel_string).group(1)


def parse_general(jewel_string: str, general_map: Dict[str, int]) -> str:
    general = re.search(r'Item Level: \d\d\n(?:-*)\n.*(\b\w+)', jewel_string).group(1)
    assert general in general_map.keys()
    return general


def parse_militant_faith_mods(jewel_string: str) -> List[str]:
    match = re.search(r'Templars\n(.*)\n(.*)', jewel_string)
    return [match.group(1), match.group(2)]


def mf_mod_int_to_strs(mf_mods: int, mod_list: Dict[str, int]) -> List[str]:
    str_mods = []
    for x in range(0, len(mod_list)):
        if (mf_mods & (2 ** x)) > 1:
            str_mods.append(list(mod_list.keys())[x])

    return str_mods


def mf_mod_strs_to_int(mf_mods: List[str], mod_map: Dict[str, int]) -> int:
    mod_int = 0
    for mod in mf_mods:
        mod_int += mod_map[mod]

    return mod_int
