import pytest
import math
from unittest.mock import Mock
from app.scripts.jewel_radius_drawing import JewelDrawing, Vertex


@pytest.mark.parametrize('a, b, maxOrbits, expected', [(0, 0, 400, 270),
                                                       (3, 1, 12, 0),
                                                       (3, 13, 16, (360 * (9 / 16))),
                                                       (5, 7, 12, 60)])
def test_calc_arc_rotation(a, b, maxOrbits, expected):
    d = JewelDrawing()
    actual = d.calc_arc_rotation(a, b, maxOrbits)
    assert actual == expected


def test_build_jewel_to_nodes_in_radius_map_jewels_relative_pos_to_self_is_zero():
    d = JewelDrawing()
    j_map = d.build_jewel_to_nodes_in_radius_map()
    for jewel in j_map:
        assert j_map[jewel].nodes[jewel].relative_coords == Vertex(0, 0)


@pytest.mark.parametrize('a, b, g, r, expected', [
    (Vertex(1, 0), Vertex(0, 1), Vertex(0, 0), 1, (math.pi) / 2),
    (Vertex(0, 1), Vertex(1, 0), Vertex(0, 0), 1, (math.pi) / 2),
    (Vertex(1518, 484.7), Vertex(1456.1, 526.1), Vertex(0, 0), 335, 74.62276959687226),
    (Vertex(1456.1, 526.1), Vertex(1518, 484.7), Vertex(0, 0), 335, 74.62276959687226)])
def test_calc_arc_len(a, b, g, r, expected):
    d = JewelDrawing()
    actual = d.adjusted_arc_len(a, b, g, r)
    assert actual == expected


def test_calc_arc_len_2():
    d = JewelDrawing()
    radius = 335
    perOrbit = 16
    angle = 360 * (abs(5 - 8) / perOrbit)
    angle = math.radians(angle)
    expected = angle * radius

    # reflexes = Mock(absolute_coords=Vertex(1725.9296433912812, 950.8039498423051))
    # minor_eva = Vertex(1416.43, 1157.605)
    # center = Vertex(1416.43, 822.605)

    reflexes = Mock(orbitIndex=5)
    minor_eva = Mock(orbitIndex=8)

    actual = d.calc_arc_len(reflexes, minor_eva, radius, perOrbit)
    assert actual == expected


@pytest.mark.parametrize('a, b, m, expected', [
    (1, 11, 12, 2), (4, 12, 12, 4), (0, 12, 12, 0), (9, 3, 12, 6)
])
def test_index_dist(a, b, m, expected):
    d = JewelDrawing()
    actual = d.index_dist(a, b, m)
    actual == expected
