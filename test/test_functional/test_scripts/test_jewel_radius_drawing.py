import pytest
from unittest.mock import Mock
from test.test_data.divayth_fyr import DIVAYTH_FYR_API
from test.test_data.brother_yide import BROTHER_YIDE_API
from app.scripts.jewel_radius_drawing import JewelDrawing


@pytest.fixture
def mock_jewel_divayth():
    yield Mock(
        jewel_type='Militant Faith',
        seed=7875,
        general='Dominus',
        mf_mods=["+2% to all Elemental Resistances per 10 Devotion",
                 "1% reduced Mana Cost of Skills per 10 Devotion"]
    )


@pytest.fixture
def mock_jewel_yide():
    yield Mock(
        jewel_type='Glorious Vanity',
        seed=2274,
        general='Doryani',
        mf_mods=None
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