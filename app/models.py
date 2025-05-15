from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, BOOLEAN, INTEGER, BIGINT, SMALLINT, JSON

metadata_obj = MetaData()

c_ = character = Table(
    'character',
    metadata_obj,
    Column('character_id', BIGINT, primary_key=True),
    Column('league_id', ForeignKey('league.league_id')),
    Column('ggg_id', Text),
    Column('character_name', Text),
    Column('class_id', ForeignKey('class_lut.class_id')),
    Column('character_level', Integer),
    Column('account_name', Text),
    Column('ladder_rank', Integer),
    Column('delve_depth', Integer),
    Column('last_scan', TIMESTAMP),
)

cl_ = class_lut = Table(
    'class_lut',
    metadata_obj,
    Column('class_id', BIGINT, primary_key=True),
    Column('base_class_name', Text),
    Column('ascendancy_class_name', Text)
)

gl_ = general_lut = Table(
    'general_lut',
    metadata_obj,
    Column('general_id', SMALLINT, primary_key=True),
    Column('general_name', Text)
)

j_ = jewel = Table(
    'jewel',
    metadata_obj,
    Column('jewel_id', BIGINT, primary_key=True),
    Column('character_id', ForeignKey('character.character_id')),
    Column('jewel_type_id', ForeignKey('jewel_type_lut.jewel_type_id')),
    Column('seed', INTEGER),
    Column('general_id', ForeignKey('general_lut.general_id')),
    Column('mf_mods', INTEGER),
    Column('socket_id', INTEGER),
    Column('drawing', JSON),
    Column('scan_date', TIMESTAMP)
)

jtl_ = jewel_type_lut = Table(
    'jewel_type_lut',
    metadata_obj,
    Column('jewel_type_id', SMALLINT, primary_key=True),
    Column('type_name', Text)
)

l_ = league = Table(
    'league',
    metadata_obj,
    Column('league_id', SMALLINT, primary_key=True),
    Column('league_name', Text),
    Column('hardcore', BOOLEAN),
    Column('league_start', TIMESTAMP),
    Column('league_end', TIMESTAMP),
)

mml_ = mf_mod_lut = Table(
    'mf_mod_lut',
    metadata_obj,
    Column('mf_mod_lut_id', SMALLINT, primary_key=True),
    Column('mod_bit', INTEGER),
    Column('mod_text', Text),
)