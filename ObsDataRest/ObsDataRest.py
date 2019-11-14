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

    def delete(self, _id):
        logging.info('%s.%s(%s)' % (self.__class__.__name__, 'delete', _id))
        if not self._model.delete()(_id):
            return '', 404
        else:
            return '', 200

class DataSources(_ODRBase):
    pass

class DataTypes(_ODRBase):
    pass

class Data(_ODRBase):
    def put(self, _source, _type, **kwargs):
        logging.info('%s.%s(%s, %s, %s)' % (self.__class__.__name__, 'put', _source, _type, request.json))
        all_jsons = request.json.get('Data', [])
        for json_entry in all_jsons:
            try:
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
            except IntegrityError:
                self._model.rollback()
                return {'error': 'Integrity violated, either duplicate record or non-existent source / type'}, 400
            except:
                self._model.rollback()
                logging.error('%s.%s() failed' % (self.__class__.__name__, 'put'), exc_info = True)
                raise
        self._model.commit()
        return '', 200

    def get(self, _source, _type, _end_date = None, _start_date = None):
        rv, rc = super(Data, self).get(self.parents['values'] + [self.offset, self.limit])
        if self.format == 'google.table':
            rv = _create_google_table(rv)
        return rv, rc

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
