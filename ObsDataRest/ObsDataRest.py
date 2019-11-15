import configparser
import os
from .model import UserModel, DataTypesModel, DataSourcesModel, DataModel
import ipaddress

from flask import Flask, request, g, abort, jsonify
from flask_restful import Resource, Api, reqparse
import logging
from datetime import datetime
from dateutil import parser

from . import app, api, db
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from flask_jwt_extended import create_access_token, jwt_required

mypath = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(os.path.join(mypath,'ObsDataRest.cfg'))
# app.config['network_read'] = config.get('network_access', 'read', fallback = None)
# app.config['network_write'] = config.get('network_access', 'write', fallback = None)
# app.config['logfile'] = config.get('log', 'path', fallback = '%s.log' % __name__)
db_file = os.path.join(mypath,config['database']['path'])

def init_db(path = None):
    if not path:
        path = getattr(g, 'db_file', db_file)
        with app.app_context():
            conn, cursor = get_conn(path, True)
            with app.open_resource('struct.sql', mode='r') as f:
                cursor.executescript(f.read())
                conn.commit()
                g.db_file = path

logging.basicConfig(
    filename = app.config.get('logfile'),
    level = logging.DEBUG,
    format = '%(asctime)s %(message)s',
)

model_classes = {
    'User': UserModel,
    'DataSources': DataSourcesModel,
    'DataTypes': DataTypesModel,
    'Data': DataModel
}

# def _limit_access(mode, remote_addr):
#     network_def = app.config.get('network_%s' % mode, None)
#     if not network_def:
#         return
#     if (ipaddress.ip_address(remote_addr) not in ipaddress.ip_network(network_def)):
#         abort(403)  # Forbidden
# @app.before_request
# def limit_remote_addr():
#     if request.method in ['PUT', 'POST', 'DELETE']:
#         mode = 'write'
#     else:
#         mode = 'read'
#     return _limit_access(mode, request.remote_addr)

class _ODRBase(Resource):
    def __init__(self):
        logging.debug('%s.__init__(), remote = %s' % (self.__class__.__name__, request.remote_addr))
        self._model = model_classes[self.__class__.__name__]
        self.cols = self._model.columns()
        super(_ODRBase, self).__init__()

    def get(self, _id = None):
        logging.info('%s.%s(%s)' % (self.__class__.__name__, 'get', _id))
        objs = self._model.get(_id)
        if _id:
            objs = [objs, ]
        logging.info('%s.%s() = %s' % (self.__class__.__name__, 'get', objs))
        if all(objs):
            return {self.__class__.__name__: [obj.to_dict(self.cols) for obj in objs]}, 200
        else:
            return {self.__class__.__name__: []}, 404

    @jwt_required
    def put(self, _id = None):
        logging.info('%s.%s(%s, %s)' % (self.__class__.__name__, 'put', _id, request.json))
        if not _id:
            return 'Please specify ID', 405
        try:
            if _id:
                existing_entry = self._model.get(_id)
            else:
                existing_entry = None
            if existing_entry:
                for col in self.cols:
                    value = request.json.get(col, None)
                    if value:
                        setattr(existing_entry, col, value)
                existing_entry.update()
                rc = 201
            else:
                logging.debug('ID: %s' % _id)
                if 'id' not in request.json:
                    request.json['id'] = _id
                new_entry = self._model.from_dict(request.json)
                new_entry.insert()
                rc = 200
        except:
            logging.error('%s.%s() failed' % (self.__class__.__name__, 'put'), exc_info = True)
            raise
        return '',rc

    @jwt_required
    def delete(self, _id):
        logging.info('%s.%s(%s)' % (self.__class__.__name__, 'delete', _id))
        if not self._model.delete(_id):
            return '', 404
        else:
            return '', 200

class DataSources(_ODRBase):
    pass

class DataTypes(_ODRBase):
    pass

class Data(_ODRBase):
    def _insert_one(self, _source, _type, json_entry):
        if 'data_type_id' not in json_entry:
            json_entry['data_type_id'] = _type
        if 'data_source_id' not in json_entry:
            json_entry['data_source_id'] = _source
        if 'entity_created' not in json_entry:
            json_entry['entity_created'] = datetime.now()
        else:
            json_entry['entity_created'] = parser.parse(json_entry['entity_created'])
        new_entry = self._model.from_dict(json_entry)
        new_entry.insert()

    @jwt_required
    def put(self, _source, _type, **kwargs):
        logging.info('%s.%s(%s, %s, %s)' % (self.__class__.__name__, 'put', _source, _type, request.json))
        all_jsons = request.json.get('Data', [])
        for json_entry in all_jsons:
            try:
                self._insert_one(_source, _type, json_entry)
            except IntegrityError:
                return {'error': 'Integrity violated, either duplicate record or non-existent source / type'}, 400
            except:
                logging.error('%s.%s() failed' % (self.__class__.__name__, 'put'), exc_info = True)
                raise
        return '', 200

    def get(self, _source, _type, _end_date = None, _start_date = None):
        if not _start_date:
            _start_date = '1900-01-01T00:00:00'
        if not _end_date:
            _end_date = '2999-12-31T00:00:00'
        # objs = self._model.get(_source, _type, parser.parse(_end_date), parser.parse(_start_date))
        objs = db.session.query(self._model)\
            .filter(self._model.data_type_id == _type)\
            .filter(self._model.data_source_id == _source)\
            .filter(self._model.entity_created >= parser.parse(_start_date))\
            .filter(self._model.entity_created <= parser.parse(_end_date))\
            .all()
        if not objs:
            return '', 404
        if not len(objs):
            return '', 404
        return {self.__class__.__name__: [obj.to_dict(self.cols) for obj in objs]}, 200

auth_parser = reqparse.RequestParser()
auth_parser.add_argument('username', help = 'This field cannot be blank', required = True)
auth_parser.add_argument('password', help = 'This field cannot be blank', required = True)

def add_user(username, password):
    user = UserModel(username = username)
    user.set_password(password)
    user.insert()

class Authorize(Resource):
    def post(self):
        data = auth_parser.parse_args()
        current_user = UserModel.find_by_username(data['username'])

        if not current_user:
            return {'message': 'Wrong credentials'}, 403

        if current_user.check_password(data['password']):
            access_token = create_access_token(identity = data['username'])
            return {
                'message': 'Logged in as {}'.format(current_user.username),
                'access_token': access_token
                }, 200
        else:
            return {'message': 'Wrong credentials'}, 403

api.add_resource(DataSources,
        '/sources/<string:_id>',
        '/sources/'
    )
api.add_resource(DataTypes,
        '/types/<string:_id>',
        '/types/'
    )
api.add_resource(Data,
        '/data/<string:_source>/<string:_type>',
        '/data/<string:_source>/<string:_type>/<string:_end_date>',
        '/data/<string:_source>/<string:_type>/<string:_end_date>/<string:_start_date>',
    )
api.add_resource(Authorize,
        '/authorize'
    )
@app.route('/data/dates/<string:_source>/<string:_type>')
def get_data_dates(_source, _type):
    logging.info('%s.%s(%s, %s)' % ('Data', 'get_dates', _source, _type))
    res = db.session.query(
        func.max(DataModel.entity_created).label('max_date'), func.min(DataModel.entity_created).label('min_date')
    ).filter(
        DataModel.data_source_id == _source
    ).filter(
        DataModel.data_type_id == _type
    ).one()
    logging.debug('%s.%s(%s, %s) = %s' % ('Data', 'get_dates', _source, _type, res))
    return {
        'min_date': res.min_date.isoformat() if res.min_date else None
        , 'max_date': res.max_date.isoformat() if res.max_date else None
    }, 200
