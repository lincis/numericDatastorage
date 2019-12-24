from flask import Flask
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy, Model
from .config import Config
from sqlalchemy import inspect
from datetime import datetime
from decimal import Decimal

from sqlalchemy.engine import Engine
from sqlalchemy import event
from flask_jwt_extended import JWTManager

from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room

class RestModel(Model):
    def insert(self, commit = True):
        db.session.add(self)
        if commit:
            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise

    def update(self):
        db.session.flush()
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

    @classmethod
    def get(cls, _id):
        if _id:
            return cls.query.get(_id)
        else:
            return cls.query.all()

    @classmethod
    def columns(cls):
        cols = []
        mapper = inspect(cls)
        for column in mapper.attrs:
            cols.append(column.key)
        return cols

    def to_dict(self, _cols):
        val_dict = {}
        for col in _cols:
            value = self.__getattribute__(col)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = float(value)
            val_dict[col] = value
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
jwt = JWTManager(app)

socketio = SocketIO(cors_allowed_origins = '*')
socketio.init_app(app, async_mode = 'eventlet', message_queue='redis://')

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if app.config.get('SQLALCHEMY_DATABASE_URI', 'None').startswith('sqlite'):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


from .model import UserModel, DataSourcesModel, DataTypesModel, DataModel
from .ObsDataRest import add_user

class NDSNamespace(Namespace):
    def on_connect(self):
        print('Hell yeah')
        emit('nds_response', {'data': 'Connected'})

    def on_select_source_type(self, message):
        print('Select data source')
        print(message)
        room = '/%s/%s' % (message['source'], message['type'])
        join_room(room)
        last_entry = db.session.query(DataModel)\
            .filter(DataModel.data_type_id == message['type'])\
            .filter(DataModel.data_source_id == message['source'])\
            .order_by(DataModel.entity_created.desc()).limit(1).all()
        emit('new_data', last_entry[0].to_dict(DataModel.columns()), namespace = '/datasocket', room = room)

socketio.on_namespace(NDSNamespace('/datasocket'))
