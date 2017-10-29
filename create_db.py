import argparse
import os
import sqlite3

parser = argparse.ArgumentParser(description='Create ObsDataRest database.')
parser.add_argument('-n', action="store", dest="db_name", help="Database file name", default="ObsDataRest.db")
parser.add_argument('-p', action="store", dest="db_path", help="Path where to create database", default=".database")
parser.add_argument('-d', action="store_true", dest="db_drop", help="Delete existing DB", default=False)
args = parser.parse_args()

db_file = os.path.join(args.db_path, args.db_name)

if args.db_drop:
    try:
        os.remove(db_file)
    except:
        pass

if not os.path.exists(args.db_path):
    os.makedirs(args.db_path)

conn = sqlite3.connect(db_file)

c = conn.cursor()

c.execute('''
    create table DataTypes
    (
        DataTypesID text,
        Name text,
        Description text,
        Units text
    );
''')
c.execute('''
    create unique index DT_PK on DataTypes(DataTypesID);
''')

c.execute('''
    create table DataSources
    (
        DataSourceID text,
        Name text,
        Description text
    );
''')
c.execute('''
    create unique index DS_PK on DataSources(DataSourceID);
''')

c.execute('''
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
c.execute('''
    create unique index D_PK on Data(DataTypeID, DataSourceID, ObsTime);
''')
