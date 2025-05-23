from sqlalchemy.sql import select
from app.db import get_engine, dict_results
from app.models import cl_, jtl_, gl_, mml_


class LutData():

    def __init__(self):
        self._class_ids = None
        self._jewel_type_ids = None
        self._mf_mod_list = None
        self._general_list = None

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
