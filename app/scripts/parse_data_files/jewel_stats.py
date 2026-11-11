import re
import logging
from typing import Dict, List, Optional

from app.scripts.parse_data_files.classes import Stat

logger = logging.getLogger('main')

# if they actually change this then strike me down chris
DEVOTION_THRESHOLD = 150

class JewelStats:
    """
    Maintains the values and order of stats we'll display to summarize what the user is getting
    from allocating the nodes affected by this jewel.
    """

    UNSCALABLE_STATS = [
        # devotion ailment immune on consecrated ground
        'Cloistered',
        # devotion arcane surge on hit
        'Zealot',
        # guaranteed onslaught on kill
        'Add Onslaught'
    ]

    def __init__(self):
        self._stats: Dict[str, Stat] = {}

    def _make_stat(self, effect_name:str, stat: str, stat_order: int, stat_vals: List[float|int], is_keystone: bool,
                   requires_devo: bool=False) -> Stat:
        index: int
        template: str

        if is_keystone:
            # we want keystones to be forced to display first in the jewel stats
            index = -3
            # use the keystone name as the stat text, I think this is sufficient
            template = effect_name
        else:
            if effect_name in self.UNSCALABLE_STATS:
                return Stat(index=stat_order, template=stat, values=[], requires_devo=requires_devo)

            index = stat_order

            parens_pattern = r'.*\(\d+(?:\.?\d+)?-\d+(?:\.?\d+)?\).*'
            if re.match(parens_pattern, stat):
                template = re.sub(parens_pattern, '{}', stat)
            else:
                # I think all of the maraketh and karui additions don't use parenthesis
                no_parens_pattern = r'\d'
                if re.match(no_parens_pattern, stat) is None:
                    err_msg = "Ran out of patterns to attempt for this stat. Is it unscalable?"
                    logger.error(err_msg)
                    logger.error(f'Params were: {effect_name}, {stat}, {stat_order}, {stat_vals}')
                    raise ValueError(err_msg)
                template = re.sub(no_parens_pattern, '{}', stat)

        return Stat(index, template, stat_vals, requires_devo)

    def add_stat(self, json_passive: dict, stat_val: Optional[List[float | int]]=None, is_keystone: bool=False) -> List[Stat]:
        if 'abyss' in json_passive['id'] and len(json_passive['sd']) > 1:
            return self._add_range_stat(json_passive, stat_val or [])

        stats = []

        for i, stat in enumerate(json_passive['sd']):
            # if there are multiple entries in sd, we need to target the correct 'stat' entry
            stat_for_sd = next(iter(filter(lambda d: d['index'] == i + 1, json_passive['stats'].values())))

            stats.append(self._make_stat(json_passive['dn'],
                                         stat,
                                         stat_for_sd['statOrder'],
                                         stat_val or [stat_for_sd['min']],
                                         is_keystone))

        for stat in stats:
            if stat.is_splittable:
                stat1, stat2 = stat.split_stat()
                self._add_stat_to_storage(stat1)
                self._add_stat_to_storage(stat2)
            else:
                self._add_stat_to_storage(stat)

        return stats

    def add_stats_from_mf_mods(self, mf_mods: List[str]):
        """ All the MF mods give some stat per 10 devotion. """

        pattern = r'(\d+\.?\d?+)'
        multiplier = self.devotion / 10
        for i, mod in enumerate(mf_mods):
            # remove the 'per 10 Devotion' suffix
            template = re.sub(r'per 10 Devotion', '', mod)
            # extract the amount per 10 devotion
            base_stat_amount = float(re.match(pattern, mod).group(0))
            base_stat_amount = int(base_stat_amount) if base_stat_amount.is_integer() else base_stat_amount
            final_amount = base_stat_amount * multiplier
            template = re.sub(pattern, '{}', template)
            # we want to list the mf mods immediately after the keystone
            self._add_stat_to_storage(Stat(-2 + i, template, [final_amount]))


    def _add_range_stat(self, json_passive: dict, stat_val: List[float|int]) -> List[Stat]:
        """
        These effects are pretty fried because they are split into 2 lines,
        one which may not have a formatting pattern and one that does.

        Only one range is actually populated, and the other will be 0.
        """
        # TODO - don't want to do this until I know for sure that there will be 2 values from the data file
        pass

    def _add_stat_to_storage(self, stat: Stat):
        # check whether the template string is already in the dict
        if stat.template in self._stats.keys():
            # just update the stat by adding to the existing value
            self._stats[stat.template] += stat
        else:
            self._stats[stat.template] = stat

    @property
    def devotion(self):
        return self._stats['+{} to Devotion'].value

    def _devo_threshold_satisfied(self, stat: Stat) -> bool:
        if not stat.requires_devo:
            return True

        devo_total = self._stats['+{} to Devotion'].value
        return devo_total >= DEVOTION_THRESHOLD

    def as_list(self) -> List[str]:
        return [str(stat) for stat in sorted(self._stats.values(),
                                             key=lambda stat: stat.index)
                                             if self._devo_threshold_satisfied(stat)]