import sqlite3
import os
import logging
import threading

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn = {}
cursor = {}

def drop_db(db_file):
    global conn
    thread = threading.get_ident()
    if thread in conn:
        conn[thread].rollback()
        conn[thread].close()
        conn[thread] = None
    if os.path.exists(db_file):
        os.remove(db_file)
        logging.debug('Remove file: %s' % db_file)

def get_conn(db_file, drop = False):
    logging.debug('%s(%s, %s)' % ('get_conn', db_file, drop))
    thread = threading.get_ident()
    global conn, cursor
    if drop:
        drop_db(db_file)
    if not thread:
        logging.debug('New connection to: %s' % db_file)
        db_path = os.path.dirname(db_file)
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        conn[thread] = sqlite3.connect(db_file)
        conn[thread].row_factory = dict_factory
        cursor[thread] = conn[thread].cursor()
        cursor[thread].execute('PRAGMA foreign_keys = ON')
    return conn[thread], cursor[thread]
