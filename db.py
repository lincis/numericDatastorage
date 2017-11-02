import sqlite3
import configparser

config = configparser.ConfigParser()
config.read("ObsDataRest.cfg")

db_file = config["database"]["path"]

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn = sqlite3.connect(db_file)
conn.row_factory = dict_factory
cursor = conn.cursor()
