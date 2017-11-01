import argparse
import os
import sqlite3
import configparser

parser = argparse.ArgumentParser(description='Create ObsDataRest database.')
# parser.add_argument('-n', action="store", dest="db_name", help="Database file name", default="ObsDataRest.db")
# parser.add_argument('-p', action="store", dest="db_path", help="Path where to create database", default=".database")

parser.add_argument('-d', action="store_true", dest="db_drop", help="Delete existing DB", default=False)
args = parser.parse_args()

config = configparser.ConfigParser()
config.read("ObsDataRest.cfg")

db_file = config["database"]["path"]
db_path = os.path.dirname(db_file)

if args.db_drop:
    try:
        os.remove(db_file)
    except:
        pass

if not os.path.exists(db_path):
    os.makedirs(db_path)

from db import cursor

cursor.execute('''
    create table DataTypes
    (
        DataTypesID text,
        Name text,
        Description text,
        Units text
    );
''')
cursor.execute('''
    create unique index DT_PK on DataTypes(DataTypesID);
''')

cursor.execute('''
    create table DataSources
    (
        DataSourceID text,
        Name text,
        Description text
    );
''')
cursor.execute('''
    create unique index DS_PK on DataSources(DataSourceID);
''')

cursor.execute('''
    create table Data
    (
        DataTypeID text,
        DataSourceID text,
        ObsTime text,
        value numeric,
        FOREIGN KEY(DataTypeID) REFERENCES DataTypes(DataTypeID),
        FOREIGN KEY(DataSourceID) REFERENCES DataSources(DataSourceID)
    );
''')
cursor.execute('''
    create unique index D_PK on Data(DataTypeID, DataSourceID, ObsTime);
''')
