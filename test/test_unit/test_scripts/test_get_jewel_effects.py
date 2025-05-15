import pytest
from unittest.mock import Mock
from app.scripts.get_jewel_effects import NodeLookup


@pytest.mark.parametrize('jewel_type, seed, notable, expected', [
    ('Militant Faith', 7875, 21958, "Smite the Heretical"),
    ('Militant Faith', 7875, 49379, "Thoughts and Prayers"),
    ('Militant Faith', 7875, 19144, "Cloistered"),
    ('Elegant Hubris', 140320, 60031, 'Purity Rebel'),
    ('Elegant Hubris', 140320, 27301, 'Laureate'),
])
def test_lookup_changed_node_replacements(jewel_type, seed, notable, expected):
    nl = NodeLookup()
    mock_notable = Mock(
        node_id=notable
    )
    effect, replaced = nl.lookup_notable_non_gv(jewel_type, seed, mock_notable)
    assert replaced
    assert effect['dn'] == expected


@pytest.mark.parametrize('jewel_type, seed, notable, expected', [
    ('Lethal Pride', 13847, 27301, ['+20 to Strength']),
    ('Brutal Restraint', 782, 27301, ['20% increased Evasion Rating'])
])
def test_lookup_changed_node_additions(jewel_type, seed, notable, expected):
    nl = NodeLookup()
    mock_notable = Mock(
        node_id=notable
    )
    effect, replaced = nl.lookup_notable_non_gv(jewel_type, seed, mock_notable)
    assert not replaced
    assert effect['sd'] == expected


def test_lookup_nodes_gv_header_size_3():
    nl = NodeLookup()
    node_id = 12033
    seed = 100
    node = Mock(node_id=node_id)

    # table = nl.build_gv_lookup_table(seed, nodes)
    effect, replaced = nl.fast_lookup_node_gv(seed, node)
    assert effect['dn'] == 'Ritual of Stillness'
    assert effect['sd'] == [
        '35% increased Cold Damage',
        'Damage Penetrates 4% Cold Resistance'
    ]
    assert replaced


def test_lookup_nodes_gv_header_size_2():
    nl = NodeLookup()
    node_id = 24544
    seed = 100
    nodes = Mock(node_id=node_id)

    effect, replaced = nl.fast_lookup_node_gv(seed, nodes)
    assert effect['dn'] == 'Lightning Damage'
    assert effect['sd'] == ['7% increased Lightning Damage']
    assert replaced


def test_lookup_nodes_gv_header_size_6():
    nl = NodeLookup()
    node_id = 27301
    seed = 2274
    node = Mock(node_id=node_id)

    effect, replaced = nl.fast_lookup_node_gv(seed, node)
    assert effect['dn'] == 'Might of the Vaal'
    assert effect['sd'] == [
        '+7% to Critical Strike Multiplier',
        '3% increased Cast Speed',
        '5% chance to Shock'
    ]
    assert replaced


def test_lookup_nodes_gv_header_size_8():
    nl = NodeLookup()
    node_id = 6799
    seed = 115
    node = Mock(node_id=node_id)

    effect, replaced = nl.fast_lookup_node_gv(seed, node)
    assert effect['dn'] == 'Legacy of the Vaal'
    assert effect['sd'] == [
        '4% increased effect of Non-Curse Auras from your Skills',
        '+10% to Fire Resistance',
        '+6% to Critical Strike Multiplier',
        '12% increased Evasion Rating',
    ]
    assert replaced


def test_lookup_nodes_gv_fractional_stat():
    nl = NodeLookup()
    node_id = 6799
    seed = 100
    node = Mock(node_id=node_id)

    effect, replaced = nl.fast_lookup_node_gv(seed, node)
    assert effect['dn'] == 'Soul Worship'
    assert effect['sd'] == [
        '9% increased maximum Energy Shield',
        '0.3% of Spell Damage Leeched as Energy Shield'
    ]
    assert replaced


def test_fast_lookup_node_gv_1_1():
    nl = NodeLookup()
    # Twin Terrors -> Cult of Fire
    node_id = 6
    seed = 100
    node = Mock(node_id=node_id)

    replacement_node, replaced = nl.fast_lookup_node_gv(seed, node)
    assert replacement_node['dn'] == 'Cult of Fire'
    assert replacement_node['sd'] == [
        '+1% to maximum Fire Resistance',
        '+29% to Fire Resistance'
    ]
    assert replaced