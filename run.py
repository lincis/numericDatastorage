import argparse
from ObsDataRest.create_db import create
from sqlite3 import OperationalError

parser = argparse.ArgumentParser(description='Run ObsDataRest instance.')
parser.add_argument('-c', action="store_true", dest="db_create", help="Attempt to create database DB", default=False)
args = parser.parse_args()

if args.db_create:
    try:
        create()
    except OperationalError:
        pass

from ObsDataRest import app
app.run()
