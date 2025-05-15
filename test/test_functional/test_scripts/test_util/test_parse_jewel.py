import pytest
from app.util import parse_jewel as pj
from app.util.lut_cache import LutData


@pytest.fixture
def config():
    import os
    from app.app_config import create_config
    config = create_config(os.environ.get('APP_CONFIG', ''))
    yield config


def test_parse_jewel_raw_str():
    expected = pj.ParsedJewel('Militant Faith',
                              '7875',
                              'Dominus',
                              ['+2% to all Elemental Resistances per 10 Devotion',
                               '1% reduced Mana Cost of Skills per 10 Devotion'],
                              None)
    ld = LutData()
    actual = pj.parse_jewel_raw_str('''Item Class: Jewels
Rarity: Unique
Militant Faith
Timeless Jewel
--------
Limited to: 1 Historic
Radius: Large
--------
Item Level: 84
--------
Carved to glorify 7875 new faithful converted by High Templar Dominus
Passives in radius are Conquered by the Templars
+2% to all Elemental Resistances per 10 Devotion
1% reduced Mana Cost of Skills per 10 Devotion
Historic
--------
They believed themselves the utmost faithful, but that conviction became oppression.
--------
Place into an allocated Jewel Socket on the Passive Skill Tree. Right click to remove from the Socket.
''', ld)
    assert expected == actual


def test_parse_jewel_json_object():
    expected = pj.ParsedJewel('Militant Faith',
                              '7875',
                              'Dominus',
                              ['+2% to all Elemental Resistances per 10 Devotion',
                               '1% reduced Mana Cost of Skills per 10 Devotion'],
                              None)
    ld = LutData()

    jewel_obj = {
            "verified": False,
            "w": 1,
            "h": 1,
            "icon": "https://web.poecdn.com/gen/image/WzI1LDE0LHsiZ"
            "iI6IjJESXRlbXMvSmV3ZWxzL1RlbXBsYXJDaXZpbGl6YXRpb24iLCJ3Ijox"
            "LCJoIjoxLCJzY2FsZSI6MX1d/09ecf8ac86/TemplarCivilization.png",
            "league": "Settlers",
            "id": "079dfd6371c9703532291e17eac01744ddb8ee723e53e0e18d11365bca278f6e",
            "name": "Militant Faith",
            "typeLine": "Timeless Jewel",
            "baseType": "Timeless Jewel",
            "rarity": "Unique",
            "ilvl": 84,
            "identified": True,
            "properties": [
                {
                    "name": "Limited to",
                    "values": [
                        [
                            "1 Historic",
                            0
                        ]
                    ],
                    "displayMode": 0
                },
                {
                    "name": "Radius",
                    "values": [
                        [
                            "Large",
                            0
                        ]
                    ],
                    "displayMode": 0,
                    "type": 24
                }
            ],
            "explicitMods": [
                "Carved to glorify 7875 new faithful converted by High Templar Dominus\nPassives in "
                "radius are Conquered by the Templars",
                "+2% to all Elemental Resistances per 10 Devotion",
                "1% reduced Mana Cost of Skills per 10 Devotion",
                "Historic"
            ],
            "descrText": "Place into an allocated Jewel Socket on the Passive Skill Tree. "
            "Right click to remove from the Socket.",
            "flavourText": [
                "They believed themselves the utmost faithful, but that conviction became oppression."
            ],
            "frameType": 3,
            "x": 6,
            "y": 0,
            "inventoryId": "PassiveJewels"
        }
    actual = pj.parse_jewel_json_object(jewel_obj, ld)
    assert expected == actual


def test_mf_mod_int_to_strs():
    lut_data = LutData()
    mod_sum = 2050
    expected = ["3% increased Effect of non-Damaging Ailments on Enemies per 10 Devotion",
                "1% increased Minion Attack and Cast Speed per 10 Devotion"]
    actual = pj.mf_mod_int_to_strs(mod_sum, lut_data.mf_mod_map)
    assert expected == actual


def test_mf_mod_strs_to_int():
    lut_data = LutData()
    mods = ["Channelling Skills deal 4% increased Damage per 10 Devotion",
            "4% increased Totem Damage per 10 Devotion"]
    expected = 32 + 16384
    actual = pj.mf_mod_strs_to_int(mods, lut_data.mf_mod_map)
    assert expected == actual
