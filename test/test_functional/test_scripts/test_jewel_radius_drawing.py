import pytest
from unittest.mock import Mock
from test.test_data.divayth_fyr import DIVAYTH_FYR_API
from test.test_data.brother_yide import BROTHER_YIDE_API
from test.test_data.brother_yide_GV_2274 import GV_2274
from test.test_data.brother_yide_LP_13847 import LP_13847
from test.test_data.icecrashele_EH_140320 import EH_13847
from test.test_data.deranged_appraiser_BR_7393 import BR_7393
from test.test_data.trk_sanctum_BR_1575 import BR_1575
from app.scripts.jewel_radius_drawing import JewelDrawing


@pytest.fixture
def mock_jewel_divayth():
    yield Mock(
        jewel_type='Militant Faith',
        seed=7875,
        general='Dominus',
        mf_mods=["+2% to all Elemental Resistances per 10 Devotion",
                 "1% reduced Mana Cost of Skills per 10 Devotion"],
        socket_id="6"
    )


@pytest.fixture
def mock_jewel_yide():
    yield Mock(
        jewel_type='Glorious Vanity',
        seed=2274,
        general='Doryani',
        mf_mods=None,
        socket_id="7"
    )


def test_make_drawing_applies_replacement_tooltip_to_notables_MF(mock_jewel_divayth):
    api_response = DIVAYTH_FYR_API
    jewel = mock_jewel_divayth

    notable_id = 19144

    expected = Mock(
        title='Cloistered',
        body=["Immune to Elemental Ailments while on Consecrated Ground if you have at least 150 Devotion"],
        replaced_title='Sentinel'
    )

    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)

    actual = drawing.nodes[notable_id].tooltip
    assert actual.title == expected.title
    assert actual.body == expected.body
    assert actual.replaced_title == expected.replaced_title


def test_make_drawing_applies_addition_to_notables_MF(mock_jewel_divayth):
    api_response = DIVAYTH_FYR_API
    jewel = mock_jewel_divayth
    notable_id = 44103

    expected = Mock(
        title='Reflexes',
        body=["+10% chance to Suppress Spell Damage",
              "+100 to Evasion Rating",
              "30% increased Evasion Rating",
              "+5 to Devotion"],
        replaced_title=None
    )

    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)

    actual = drawing.nodes[notable_id].tooltip
    assert actual.title == expected.title
    assert actual.body == expected.body
    assert actual.replaced_title == expected.replaced_title


def test_make_drawing_applies_replacement_to_keystones_MF(mock_jewel_divayth):
    api_response = DIVAYTH_FYR_API
    jewel = mock_jewel_divayth
    keystone_id = 12926

    expected = Mock(
        title='Inner Conviction',
        body=["3% more Spell Damage per Power Charge",
              "Gain Power Charges instead of Frenzy Charges"],
        replaced_title="Iron Grip"
    )

    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)

    actual = drawing.nodes[keystone_id].tooltip
    assert actual.title == expected.title
    assert actual.body == expected.body
    assert actual.replaced_title == expected.replaced_title


def test_make_drawing_applies_additions_to_small_passives_MF(mock_jewel_divayth):
    api_response = DIVAYTH_FYR_API
    jewel = mock_jewel_divayth
    node_id = 22061

    expected = Mock(
        title='Mana',
        body=["+25 to maximum Mana",
              "10% increased maximum Mana",
              "+5 to Devotion"],
        replaced_title=None
    )

    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)

    actual = drawing.nodes[node_id].tooltip
    assert actual.title == expected.title
    assert actual.body == expected.body
    assert actual.replaced_title == expected.replaced_title


def test_make_drawing_applies_replacement_to_small_passives_MF(mock_jewel_divayth):
    api_response = DIVAYTH_FYR_API
    jewel = mock_jewel_divayth
    node_id = 28330

    expected = Mock(
        title='Devotion',
        body=["+10 to Devotion"],
        replaced_title='Strength'
    )

    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)

    actual = drawing.nodes[node_id].tooltip
    assert actual.title == expected.title
    assert actual.body == expected.body
    assert actual.replaced_title == expected.replaced_title


def test_make_drawing_includes_mf_stats_in_tooltip(mock_jewel_divayth):
    api_response = DIVAYTH_FYR_API
    jewel = mock_jewel_divayth
    node_id = 31683

    expected = Mock(
        title='Militant Faith',
        body=["Carved to glorify 7875 new faithful converted by High Templar Dominus",
              "Passives in radius are Conquered by the Templars",
              "+2% to all Elemental Resistances per 10 Devotion",
              "1% reduced Mana Cost of Skills per 10 Devotion",
              'Historic'],
        replaced_title=None
    )

    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)

    actual = drawing.nodes[node_id].tooltip
    assert actual.title == expected.title
    assert actual.body == expected.body
    assert actual.replaced_title == expected.replaced_title


def test_make_drawing_applies_basic_replacement_to_notables_GV(mock_jewel_yide):
    api_response = BROTHER_YIDE_API
    jewel = mock_jewel_yide
    node_id = 57900

    expected = Mock(
        title='Flesh to Lightning',
        body=["29% increased Lightning Damage", "10% of Physical Damage Converted to Lightning Damage"],
        replaced_title='Command of Steel'
    )

    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)

    actual = drawing.nodes[node_id].tooltip
    assert actual.title == expected.title
    assert actual.body == expected.body
    assert actual.replaced_title == expected.replaced_title


def test_make_drawing_applies_root_jewel_tooltip_non_MF(mock_jewel_yide):
    api_response = BROTHER_YIDE_API
    jewel = mock_jewel_yide
    node_id = 28475

    expected = Mock(
        title='Glorious Vanity',
        body=["Bathed in the blood of 2274 sacrificed in the name of Doryani",
              "Passives in radius are Conquered by the Vaal",
              'Historic'],
        replaced_title=None
    )

    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)

    actual = drawing.nodes[node_id].tooltip
    assert actual.title == expected.title
    assert actual.body == expected.body
    assert actual.replaced_title == expected.replaced_title


def test_make_drawing_applies_jewel_type(mock_jewel_yide):
    api_response = BROTHER_YIDE_API
    jewel = mock_jewel_yide
    expected = 'Glorious Vanity'

    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)
    assert drawing.jewel_type == expected


def test_make_drawing_applied_stat_total(mock_jewel_divayth):
    api_response = DIVAYTH_FYR_API
    jewel = mock_jewel_divayth

    expected = set([
        '+115 to Devotion',
        'Immune to Elemental Ailments while on Consecrated Ground if you have at least 150 Devotion',
        '+22% to all Elemental Resistances',
        '11% reduced Mana Cost of Skills'
    ])

    jd = JewelDrawing()
    stats = jd.make_drawing(api_response, jewel).jewel_stats
    assert set(stats) == expected


def test_make_drawing_applied_stat_total_GV():
    api_response = GV_2274
    jewel = Mock(
        jewel_type='Glorious Vanity',
        seed=2274,
        general='Doryani',
        mf_mods=None,
        socket_id="7"
    )

    expected = set([
        '16% increased Fire Damage',
        '12% increased Mana Regeneration Rate',
        '2% increased Movement Speed',
        '+2% Chance to Block Attack Damage',
        '12% increased Projectile Damage',
        '37% increased Lightning Damage',
        '10% of Physical Damage Converted to Lightning Damage',
        '20% increased Cold Damage',
        '+11% to Lightning Resistance',
        '2% increased Effect of your Curses'
    ])
    
    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)
    assert set(drawing.jewel_stats) == expected


def test_make_drawing_applied_stat_total_LP():
    api_response = LP_13847
    jewel = Mock(
        jewel_type='Lethal Pride',
        seed=13847,
        general='Akoya',
        mf_mods=None,
        socket_id="16"
    )

    expected = set([
        '60% increased Melee Critical Strike Chance',
        '5% chance to deal Double Damage',
        '+32 to Strength'
    ])

    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)
    assert set(drawing.jewel_stats) == expected


def test_make_drawing_applied_stat_total_EH():
    api_response = EH_13847
    jewel = Mock(
        jewel_type='Elegant Hubris',
        seed=140320,
        general='Caspiro',
        mf_mods=None,
        socket_id="18"
    )

    expected = set([
        '+50% to Cold Resistance',
        '80% increased Armour',
        '15% increased Attack Speed',
        '16% increased Armour per Endurance Charge',
        'Minions deal 160% increased Damage',
        '50% increased Damage with Bleeding',
        'Bleeding you inflict deals Damage 10% faster'
    ])

    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)
    assert set(drawing.jewel_stats) == expected


def test_make_drawing_applied_stat_total_BR():
    api_response = BR_7393
    jewel = Mock(
        jewel_type='Brutal Restraint',
        seed=7393,
        general='Nasima',
        mf_mods=None,
        socket_id='4'
    )

    expected = set([
        '10% increased Duration of Elemental Ailments on Enemies',
        '40% increased Evasion Rating',
        '5% increased Movement Speed',
        'You gain Onslaught for 8 seconds on Kill',
        '10% increased Dexterity',
        "25% chance to gain Alchemist's Genius when you use a Flask",
        '10% increased Flask Charges gained',
        '+64 to Dexterity'
    ])

    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)
    assert set(drawing.jewel_stats) == expected


def test_make_drawing_BR_1575():
    api_response = BR_1575
    jewel = Mock(
        jewel_type='Brutal Restraint',
        seed=1575,
        general='Balbala',
        mf_mods=None,
        socket_id='18'
    )

    jd = JewelDrawing()
    drawing = jd.make_drawing(api_response, jewel)
    assert drawing