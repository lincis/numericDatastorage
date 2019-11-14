from flask import Flask
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy, Model
from .config import Config
from sqlalchemy import inspect

from sqlalchemy.engine import Engine
from sqlalchemy import event

class RestModel(Model):
    def insert(self, commit = True):
        db.session.add(self)
        if commit:
            db.session.commit()

    @staticmethod
    def commit():
        db.session.commit()

    @staticmethod
    def rollback():
        db.session.rollback()

    def update(self):
        db.session.flush()
        db.session.commit()

    @classmethod
    def get(cls, _id):
        if _id:
            return cls.query.get(_id)
        else:
            return cls.query.all()

    @classmethod
    def columns(cls):
        print(cls)
        cols = []
        mapper = inspect(cls)
        for column in mapper.attrs:
            cols.append(column.key)
        return cols

    def to_dict(self, _cols):
        val_dict = {}
        for col in _cols:
            val_dict[col] = self.__getattribute__(col)
        return val_dict

    @classmethod
    def from_dict(cls, _dict):
        try:
            return cls(**_dict)
        except:
            mapper = inspect(cls)
            values = {}
            mapper = inspect(cls)
            for column in mapper.attrs:
                values[column] = _dict.get(column, None)
            return cls(**values)

    @classmethod
    def delete(cls, _id):
        obj = cls.query.get(_id)
        if not obj:
            return False
        db.session.delete(obj)
        db.session.commit()
        return True

app = Flask(__name__)
app.config.from_object(Config)
api = Api(app)
db = SQLAlchemy(model_class = RestModel)
db.init_app(app)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if app.config.get('SQLALCHEMY_DATABASE_URI', 'None').startswith('sqlite'):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


from .model import UserModel, DataSourcesModel, DataTypesModel, DataModel
from .ObsDataRest import init_db
