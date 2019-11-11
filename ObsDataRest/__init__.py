from flask import Flask
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy
from .config import Config

app = Flask(__name__)
app.config.from_object(Config)
api = Api(app)
db = SQLAlchemy()
db.init_app(app)


from .model import User, DataSources, DataTypes, Data
from .ObsDataRest import init_db
