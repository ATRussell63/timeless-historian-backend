from typing import List, Dict
from sqlalchemy.sql import select, false
from app.db import get_engine, dict_results
from app.models import cl_, jtl_, gl_, mml_, sl_


class LutData:

    def __init__(self):
        self._class_ids = None
        self._base_classes = None
        self._jewel_type_ids = None
        self._mf_mod_list = None
        self._general_list = None
        self._abyss_domain_list = None
        self._socket_node_id_list = None
        self._socket_to_node_map = None

    @property
    def class_ids(self) -> dict:
        if self._class_ids:
            return self._class_ids

        else:
            with get_engine().connect() as conn:
                results = conn.execute(select(cl_.c.ascendancy_class_name, cl_.c.class_id)).fetchall()
                results = dict_results(results)
                self._class_ids = {row['ascendancy_class_name']: row['class_id'] for row in results}
                return self._class_ids

    @property
    def base_classes(self) -> dict:
        if self._base_classes:
            return self._base_classes

        else:
            with get_engine().connect() as conn:
                results = conn.execute(select(cl_.c.ascendancy_class_name, cl_.c.base_class_name)).fetchall()
                results = dict_results(results)
                self._base_classes = {row['ascendancy_class_name']: row['base_class_name'] for row in results}
                return self._base_classes

    @property
    def jewel_type_ids(self) -> dict:
        if self._jewel_type_ids:
            return self._jewel_type_ids

        else:
            with get_engine().connect() as conn:
                results = conn.execute(select(jtl_.c.type_name, jtl_.c.jewel_type_id)).fetchall()
                results = dict_results(results)
                self._jewel_type_ids = {row['type_name']: row['jewel_type_id'] for row in results}
                return self._jewel_type_ids

    @property
    def mf_mod_map(self) -> dict:
        if self._mf_mod_list:
            return self._mf_mod_list

        else:
            with get_engine().connect() as conn:
                results = conn.execute(select(mml_.c.mod_text, mml_.c.mod_bit)).fetchall()
                results = dict_results(results)
                self._mf_mod_list = {row['mod_text']: row['mod_bit'] for row in results}
                return self._mf_mod_list

    @property
    def general_list(self) -> dict:
        if self._general_list:
            return self._general_list

        else:
            with get_engine().connect() as conn:
                results = conn.execute(select(gl_.c.general_name, gl_.c.general_id)).fetchall()
                results = dict_results(results)
                self._general_list = {row['general_name']: row['general_id'] for row in results}
                return self._general_list

    @property
    def abyss_domain_list(self) -> List[str]:
        if self._abyss_domain_list:
            return self._abyss_domain_list

        else:
            with get_engine().connect() as conn:
                results = conn.execute(select(jtl_.c.type_name).where(jtl_.c.is_abyss_domain_jewel == false())).fetchall()
                results = dict_results(results)
                self._abyss_domain_list = [row['type_name'] for row in results]
                return self._abyss_domain_list

    @property
    def socket_to_node_map(self) -> Dict[int, dict]:
        if self._socket_to_node_map:
            return self._socket_to_node_map

        else:
            with get_engine().connect() as conn:
                results = conn.execute(select(sl_)).fetchall()
                results = dict_results(results)
                self._socket_to_node_map = {row['socket_id']: row for row in results}
                return self._socket_to_node_map

    @property
    def socket_id_list(self) -> List[int]:
        return [row['socket_id'] for row in self.socket_to_node_map.values()]