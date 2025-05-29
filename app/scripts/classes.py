from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Vertex:
    x: float
    y: float

    def __eq__(self, value):
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
class NodeTooltip:
    title: str
    body: List[str]
    replaced_title: str


@dataclass
class Node:
    name: str
    node_id: int
    node_type: str
    allocated: bool
    absolute_coords: Vertex
    relative_coords: Optional[Vertex]
    mods: Optional[List[str]]
    reminder: Optional[List[str]]
    orbit: int
    orbitIndex: int
    orbitRadius: int
    connected_nodes: List[int]
    group_id: int
    group_absolute_coords: Vertex
    group_relative_coords: Optional[Vertex]
    tooltip: Optional[NodeTooltip]


@dataclass
class StraightEdge:
    allocated: bool
    ends: List[Dict]


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
    jewel_stats: Optional[List[str]]
    api_idx: int
    jewel_coords: Vertex
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