import sqlite3
import os

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn = cursor = None

def get_conn(db_file, drop = False):
    global conn, cursor
    if drop:
        if conn:
            conn.close()
            conn = None
        if os.path.exists(db_file):
            os.remove(db_file)
    if not (conn or cursor):
        db_path = os.path.dirname(db_file)
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        conn = sqlite3.connect(db_file)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
    return conn, cursor
