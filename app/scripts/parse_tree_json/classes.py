import math
from dataclasses import dataclass
from typing import List, Optional
from app.scripts.drawing.jewel_radius_drawing import Vertex

@dataclass
class Stat:
    index: int
    template: str
    value: Optional[float]

    def format_stat(self) -> str:
        if self.value is not None:
            truncated_val = int(self.value) if self.value.is_integer() else self.value
            return self.template.format(truncated_val)
        else: # not scalable
            return self.template

@dataclass
class NodeTooltip:
    title: str
    body: List[str]
    replaced_title: Optional[str]

@dataclass
class Anchor:
    id: int
    global_x: float
    global_y: float
    local_x: Optional[float]
    local_y: Optional[float]
    radius: int
    angle: float


@dataclass
class ConnectedNodes:
    path_out: List[int]
    path_in: List[int]


@dataclass
class Node:
    node_id: int
    name: str
    allocated: Optional[bool]
    tags: List[str]
    ascendancy: Optional[str]
    stats: List[str]
    reminder_text: List[str]
    anchor: Anchor
    absolute_coordinates: Optional[Vertex]
    relative_coordinates: Optional[Vertex]
    connected_nodes: ConnectedNodes
    tooltip: Optional[NodeTooltip]

    def has_tag(self, tag: str):
        return tag in self.tags

    def all_connected(self):
        return list(set(self.connected_nodes.path_out
                        + self.connected_nodes.path_in))

    def find_absolute_coordinates(self):
        x = (math.cos(self.anchor.angle) * self.anchor.radius) + self.anchor.global_x
        y = (math.sin(self.anchor.angle) * self.anchor.radius) + self.anchor.global_y

        self.absolute_coordinates = Vertex(x, y)

    def make_tooltip(self, effect_name: str, effect_mod_lines: List[str], effect_stats: dict, replaced: bool):
        # todo - gonna do the formatting in here

        if replaced:
            self.tooltip = NodeTooltip(
                title=effect_name,
                body=effect_mod_lines,
                replaced_title=self.name
            )
        else:
            self.tooltip = NodeTooltip(
                title=self.name,
                body=self.stats + effect_mod_lines,
                replaced_title=None
            )