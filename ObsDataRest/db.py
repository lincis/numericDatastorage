import sqlite3
import os
import logging

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn = cursor = None

def drop_db(db_file):
    global conn, cursor
    if conn:
        conn.rollback()
        conn.close()
        conn = None
    if os.path.exists(db_file):
        os.remove(db_file)
        logging.debug('Remove file: %s' % db_file)

def get_conn(db_file, drop = False):
    logging.debug('%s(%s, %s)' % ('get_conn', db_file, drop))
    global conn, cursor
    if drop:
        drop_db(db_file)
    if not (conn or cursor):
        logging.debug('New connection to: %s' % db_file)
        db_path = os.path.dirname(db_file)
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        conn = sqlite3.connect(db_file)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')
    return conn, cursor
