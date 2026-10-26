from typing import Dict, List

from tree_data import TREE_JSON

class TreeConstants:

    def __init__(self):
        self._skills_per_orbit_map = None
        self._orbit_radii = None
        self._jewel_slots = None

    def skills_per_orbit(self, idx: int) -> Dict[int, int]:
        if self._skills_per_orbit_map is None:
            orbits_list = TREE_JSON['constants']['skillsPerOrbit']
            self._skills_per_orbit_map = {i: val for i, val in enumerate(orbits_list)}

        return self._skills_per_orbit_map[idx]

    def orbit_radius(self, idx: int) -> Dict[int, int]:
        if self._orbit_radii is None:
            orbits_list = TREE_JSON['constants']['orbitRadii']
            self._orbit_radii = {i: val for i, val in enumerate(orbits_list)}

        return self._orbit_radii[idx]

    @property
    def jewel_slots(self) -> List[int]:
        if self._jewel_slots is None:
            self._jewel_slots = TREE_JSON['jewelSlots']

        return self._jewel_slots