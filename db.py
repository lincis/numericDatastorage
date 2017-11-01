import sqlite3
import configparser

config = configparser.ConfigParser()
config.read("ObsDataRest.cfg")

db_file = config["database"]["path"]
conn = sqlite3.connect(db_file)
cursor = conn.cursor()
