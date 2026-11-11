import math
from dataclasses import dataclass
from typing import List, Optional

from app.scripts.classes import Vertex
from app.scripts.parse_data_files.nodes import Tag

STRENGTH = ("+{} to Strength", 9000011)
DEXTERITY = ("+{} to Dexterity", 9000012)
INTELLIGENCE = ("+{} to Intelligence", 9000013)
FIRE_RES = ("+{}% to Fire Resistance", 9000001)
COLD_RES = ("+{}% to Cold Resistance", 9000002)
LIGHT_RES = ("+{}% to Lightning Resistance", 9000003)

SPLITTABLE_STATS = {
    "+{} to Strength and Intelligence": (STRENGTH, INTELLIGENCE),
    "+{} to Strength and Dexterity": (STRENGTH, DEXTERITY),
    "+{} to Dexterity and Intelligence": (DEXTERITY, INTELLIGENCE),
    "+{}% to Fire and Cold Resistance": (FIRE_RES, COLD_RES),
    "+{}% to Cold and Lightning Resistance": (COLD_RES, LIGHT_RES),
    "+{}% to Fire and Lightning Resistance": (FIRE_RES, LIGHT_RES)
}

@dataclass
class Stat:
    index: int
    template: str
    values: List[float]
    requires_devo: bool=False

    @property
    def is_range_stat(self) -> bool:
        return len(self.values) == 2

    @property
    def is_mono_stat(self) -> bool:
        return len(self.values) == 1

    @property
    def value(self):
        if self.is_mono_stat:
            return self.values[0]
        elif self.is_range_stat:
            return self.values[0], self.values[1]
        else:
            return None

    def __add__(self, other):
        if not self.values or len(self.values) == 0:
            self.values = other.values
        else:
            self.values[0] += other.values[0]
            if len(self.values) > 1:
                self.values[1] += other.values[1]

    def __repr__(self) -> str:
        if self.value is None:
            return self.template
        elif self.is_mono_stat:
            truncated_val = int(self.value) if self.value.is_integer() else self.value
            return self.template.format(truncated_val)
        elif self.is_range_stat:
            val1, val2 = self.value
            truncated_val1 = int(val1) if val1.is_integer() else val1
            truncated_val2 = int(val2) if val2.is_integer() else val2
            return self.template.format(truncated_val1, truncated_val2)
        else:
            raise ValueError("Too many stats! How did that happen?")

    @property
    def is_splittable(self):
        return self.template in SPLITTABLE_STATS.keys() and self.is_mono_stat

    def split_stat(self):
        if not self.is_splittable:
            raise ValueError("This stat is not splittable, don't call me")

        stat_food1, stat_food2 = SPLITTABLE_STATS[self.template]
        return Stat(stat_food1[1], stat_food1[0], self.value), Stat(stat_food2[1], stat_food2[0], self.value)

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
    tags: List[Tag]
    ascendancy: Optional[str]
    stats: List[str]
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

    @property
    def coords(self):
        if self.absolute_coordinates is None:
            self.find_absolute_coordinates()

        return self.absolute_coordinates

    def make_tooltip_from_addition(self, added_stat: List[Stat]):
        self.tooltip = NodeTooltip(
            title=self.name,
            body = self.stats + [str(stat) for stat in sorted(added_stat, key=lambda s: s.index)],
            replaced_title = None)

    def make_tooltip_from_replacement(self, new_name: str, stats: List[Stat]):
        self.tooltip = NodeTooltip(
            title=new_name,
            body = [str(stat) for stat in sorted(stats, key=lambda s: s.index)],
            replaced_title=self.name)