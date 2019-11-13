import configparser
import os
from .model import User, DataTypes, DataSources, Data
import ipaddress

from flask import Flask, request, g, abort, jsonify
from flask_restful import Resource, Api, reqparse
import logging
from datetime import datetime
from dateutil import parser

from . import app, api, db, User, DataTypes, DataSources, Data

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
    'User': User,
    'DataSources': DataSources,
    'DataTypes': DataTypes,
    'Data': Data
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

class  DataSources(_ODRBase):
    pass

class DataTypes(_ODRBase):
    pass

def _create_google_table(raw_data):
    cols = []
    values = {}
    for row in raw_data['Data']:
        col_name = '.'.join([row['DataSourceID'], row['DataTypeID']])
        if col_name not in cols:
            cols.append(col_name)
        if not row['DateTime'] in values:
            values[row["DateTime"]] = [float('NaN') for i in range(len(cols))]
        values[row["DateTime"]][cols.index(col_name)] = float(row['Value'])
    rv = {}
    rv['cols'] = [{'id':'DateTime', 'label': 'DateTime', 'pattern': '', 'type': 'date'}]
    rv['cols'] += [{'id': col, 'label': col, 'pattern': '', 'type': 'number'} for col in cols]
    rv['rows'] = [{'c': [{'v': time},] + [{'v': v} for v in value] + [{'v': float('NaN')} for i in range(len(cols)-len(value))]} for time, value in values.items()]
    return rv

class Data(_ODRBase):

    def __init__(self):
        super(Data, self).__init__()
        self.data_sources = DataSources()
        self.data_types = DataTypes()
        self._parse_args()
        self.id_names = ['DataTypeID', 'DataSourceID', 'DateTime']
        self.parents = {'names': [], 'values': []}
        for _id in self.id_names:
            if getattr(self, _id, None):
                self.parents['values'].append(getattr(self, _id))
                self.parents['names'].append(_id)
        self.q_check = 'select %s from %s where %s = ? and %s = ? and %s = ?' % ('Value', self.table, *self.id_names)
        if len(self.parents['names']):
            where_clause = 'where %s' % ' and '.join([s + ' = ? ' for s in self.parents['names']])
        else:
            where_clause = ''
        self.q_get_id = 'select * from %s %s LIMIT ?, ?' % (self.table, where_clause)

    def _parse_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument('DataSourceID', type = str)
        parser.add_argument('DataTypeID',   type = str)
        parser.add_argument('offset',       type = int, default = 0)
        parser.add_argument('limit',        type = int, default = 50)
        parser.add_argument('format',       type = str, default = 'raw_data')
        args = parser.parse_args()
        self.DataSourceID = args.get('DataSourceID', None)
        self.DataTypeID = args.get('DataTypeID', None)
        self.offset = args.get('offset', 0)
        self.limit = args.get('limit', 50)
        self.format = args.get('format', 'raw')

    def put(self, _id = None):
        logging.info('%s.%s(%s, %s, %s)' % (self.__class__.__name__, 'put', self.DataSourceID, self.DataTypeID, request.json))
        time = request.json.get('DateTime', None)
        value = request.json.get('Value', None)
        if not (self.DataTypeID and self.DataSourceID and value != None):
            return 'Please specify data source, type and value', 400
        if not self.data_sources._check_entry([self.DataSourceID, ]):
            return 'Invalid DataSourceID = %s' % self.DataSourceID, 400
        if not self.data_types._check_entry([self.DataTypeID, ]):
            return 'Invalid DataTypeID = %s' % self.DataTypeID, 400
        if not isinstance(value, list):
            value = [value,]
        if not isinstance(time, list):
            time = [time,]
        try:
            for t, v in zip(time,value):
                if not t:
                    t = datetime.now()
                else:
                    t = parser.parse(t)
                if self._check_entry([self.DataTypeID, self.DataSourceID, t]):
                    query = 'update %s set value = ? where %s = ? and %s = ? and %s = ?' % (self.table, *self.id_names)
                    bind = [v, self.DataTypeID, self.DataSourceID, t]
                else:
                    query = 'insert into %s values (?, ?, ?, ?)' % (self.table)
                    bind = [self.DataTypeID, self.DataSourceID, t, v]
                self.cursor.execute(query, bind)
            self.conn.commit()
        except:
            logging.error('%s.%s() failed' % (self.__class__.__name__, 'put'), exc_info = True)
            raise

    def get(self, _id = None):
        rv, rc = super(Data, self).get(self.parents['values'] + [self.offset, self.limit])
        if self.format == 'google.table':
            rv = _create_google_table(rv)
        return rv, rc

api.add_resource(DataSources,
        '/sources/<_id>',
        '/sources/'
    )
api.add_resource(DataTypes,
        '/types/<_id>',
        '/types/'
    )
api.add_resource(Data,
        '/data/',
    )
