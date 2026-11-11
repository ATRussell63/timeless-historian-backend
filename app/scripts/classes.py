from dataclasses import dataclass
from typing import Dict, List, Optional
from numpy import inf
from math import isclose

from app.scripts.parse_data_files.classes import Node, Stat
from app.scripts.parse_data_files.jewel_stats import JewelStats
from app.util.utils import truncate_float

@dataclass(frozen=True)
class Vertex:
    x: float
    y: float

    def __eq__(self, value):
        if not isinstance(value, Vertex):
            raise TypeError
        return value.x == self.x and value.y == self.y

    def __sub__(self, other):
        if not isinstance(other, Vertex):
            raise TypeError
        else:
            return Vertex(x=self.x - other.x,
                          y=self.y - other.y)

    def __rsub__(self, other):
        if not isinstance(other, Vertex):
            raise TypeError
        else:
            return Vertex(x=other.x - self.x,
                          y=other.y - self.y)


@dataclass
class StraightEdge:
    allocated: bool
    ends: List[Vertex]

    def slope(self):
        # use bottom extrema as 'start' node in calculations
        # so that all slopes agree on what direction is positive
        vert1, vert2 = (self.ends[0], self.ends[1]) if self.ends[0].y <= self.ends[1].y \
                  else (self.ends[1], self.ends[0])

        y1 = vert1.y
        y2 = vert2.y
        delta_y = y2 - y1
        x1 = vert1.x
        x2 = vert2.x
        delta_x = x2 - x1

        if isclose(delta_x, 0):
            return inf

        return truncate_float(delta_y / delta_x, 1)

@dataclass
class CurvedEdge:
    allocated: bool
    relative_center: Vertex
    rotation: float
    radius: float
    angle: float


@dataclass
class DrawingRoot:
    jewel_type: Optional[str]
    jewel_id: int
    jewel_stats: JewelStats
    api_idx: int
    radius: int
    nodes: Dict[int, Node]
    curved_edges: Optional[List[CurvedEdge]]
    straight_edges: Optional[List[StraightEdge]]


@dataclass
class Jewel:
    jewel_id: int
    character_id: int
    jewel_type: str
    seed: int
    general: str
    mf_mods: List[str]
    socket_id: int
    drawing: Optional[Dict]