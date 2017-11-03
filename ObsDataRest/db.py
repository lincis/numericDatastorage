import sqlite3
import configparser
import os

mypath = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(os.path.join(mypath,"ObsDataRest.cfg"))

db_file = os.path.join(mypath,config["database"]["path"])

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn = cursor = None

def get_conn():
    global conn, cursor
    if not (conn or cursor):
        conn = sqlite3.connect(db_file)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
    return conn, cursor
