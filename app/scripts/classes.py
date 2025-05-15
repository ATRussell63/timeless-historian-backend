from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Vertex():
    x: float
    y: float

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
class DrawingRoot:
    jewel_id: int
    api_idx: int
    jewel_coords: Vertex
    radius: int
    nodes: Dict[int, Node]
    edges: Optional[List]


@dataclass
class StraightEdge:
    start: int
    end: int
    edge_type: str
    ends: List[Dict[str, Vertex]]


@dataclass
class CurvedEdge:
    start: int
    end: int
    edge_type: str
    # might cause problems
    absolute_center: Vertex
    relative_center: Vertex
    rotation: float
    arc_len: float
    radius: float
    angle: float


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