from sqlalchemy import MetaData, Table, Column
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.types import Integer, Text
from config import connection_string
import os


engine = create_engine(connection_string, max_identifier_length=128, pool_pre_ping=True)
connection = engine.raw_connection()
session = Session(engine)
metadata = MetaData(bind=engine)
Base = automap_base(metadata=metadata)
metadata.reflect(engine, views=True)


class PackTable(Base):
    __table__ = Table('stratigraphy_sludge', metadata,
                      Column("id", Integer, primary_key=True),
                      autoload=True, schema='wellref', extend_existing=True)


class SynonymTable(Base):
    __table__ = Table('stratigraphy_sludge_synonym', metadata,
                      Column("stratigraphy_sludge_id", Integer, primary_key=True),
                      autoload=True, schema='wellref', extend_existing=True)


class FieldViewTable(Base):
    __table__ = Table('field_with_synonym', metadata,
                      Column("id", Integer, primary_key=True),
                      Column("name", Text),
                      schema='wellref', extend_existing=True)


class WellInfoTable(Base):
    __table__ = Table('well_info', metadata,
                      Column("wellid", Integer, primary_key=True),
                      autoload=True, schema='well', extend_existing=True)


class ZakLoadRegisterTable(Base):
    __table__ = Table('zakloadfilesregister', metadata,
                      Column("fileid", Integer, primary_key=True),
                      autoload=True, schema='well', extend_existing=True)


class ZakIrTable(Base):
    __table__ = Table('zak_ir', metadata,
                      Column("recid", Integer, primary_key=True),
                      autoload=True, schema='well', extend_existing=True)


class SludgeHdrTable(Base):
    __table__ = Table('well_sludge_hdr', metadata,
                      Column("id", Integer, primary_key=True),
                      autoload=True, schema='well', extend_existing=True)


class SludgeLasTable(Base):
    __table__ = Table('well_sludge_las', metadata,
                      Column("id", Integer, primary_key=True),
                      autoload=True, schema='well', extend_existing=True)


class SludgeDataTable(Base):
    __table__ = Table('well_sludge_data', metadata,
                      Column("id", Integer, primary_key=True),
                      autoload=True, schema='well', extend_existing=True)


class SludgeReportTable(Base):
    __table__ = Table('well_sludge_report', metadata,
                      Column("id", Integer, primary_key=True),
                      autoload=True, schema='well', extend_existing=True)


Base.prepare()
