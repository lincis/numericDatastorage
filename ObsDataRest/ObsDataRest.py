import configparser
import os
from .model import User, DataTypes, DataSources, Data
import ipaddress

from flask import Flask, request, g, abort, jsonify
from flask_restful import Resource, Api, reqparse
import logging
from datetime import datetime
from dateutil import parser
from sqlalchemy import inspect, exists

from . import app, api, db, User, DataTypes, DataSources, Data

mypath = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(os.path.join(mypath,'ObsDataRest.cfg'))
app.config['network_read'] = config.get('network_access', 'read', fallback = None)
app.config['network_write'] = config.get('network_access', 'write', fallback = None)
app.config['logfile'] = config.get('log', 'path', fallback = '%s.log' % __name__)
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

def _limit_access(mode, remote_addr):
    network_def = app.config.get('network_%s' % mode, None)
    if not network_def:
        return
    if (ipaddress.ip_address(remote_addr) not in ipaddress.ip_network(network_def)):
        abort(403)  # Forbidden
@app.before_request
def limit_remote_addr():
    if request.method in ['PUT', 'POST', 'DELETE']:
        mode = 'write'
    else:
        mode = 'read'
    return _limit_access(mode, request.remote_addr)

class _ODRBase(Resource):
    def __init__(self):
        logging.debug('%s.__init__(), remote = %s' % (self.__class__.__name__, request.remote_addr))
        self._model = model_classes[self.__class__.__name__]
        # self.conn, self.cursor = get_conn(getattr(g, 'db_file', db_file))
        # self.table = self.__class__.__name__
        # self.id_name = self.table[:-1] + 'ID'
        # self.q_get_id = 'select * from %s where %s = ?' % (self.table, self.id_name)
        # logging.debug('q_get_id: %s' % self.q_get_id)
        # self.q_get_all = 'select * from %s' % self.table
        # logging.debug('q_get_all: %s' % self.q_get_all)
        # query = self.cursor.execute('PRAGMA table_info (%s)' % (self.table,))
        # struct = query.fetchall()
        # self.cols = []
        # for col in struct:
        #     self.cols.append(col['name'])
        # self.q_put_new = 'insert into %s values (%s)' % (self.table, ','.join(['?' for i in range(len(self.cols))]))
        # logging.debug('q_put_new: %s' % self.q_put_new)
        # self.q_put_update = 'update %s set %s where %s = ?' % (
        #     self.table,
        #     ' = ?,'.join(self.cols) + ' = ?',
        #     self.id_name
        # )
        # logging.debug('q_put_update: %s' % self.q_put_update)
        # self.q_delete = 'delete from %s where %s = ?' % (self.table, self.id_name)
        # logging.debug('q_delete: %s' % self.q_delete)
        # self.q_check = 'select %s from %s where %s = ?' % (self.id_name, self.table, self.id_name)
        self.cols = []
        mapper = inspect(self._model)
        for column in mapper.attrs:
            self.cols.append(column.key)
        super(_ODRBase, self).__init__()

    def _check_entry(self,_id):
        rv = bool(self._model.query.filter(id == _id))
        logging.debug('%s.%s(%s): %s' % (self.__class__.__name__, '_check_entry', _id, rv))
        return rv

    def _get(self, _id):
        logging.debug('%s.%s(%s)' % (self.__class__.__name__, '_get', _id))
        try:
            if _id:
                # rv = self._model.query.filter_by(id = _id).first()
                rv = self._model.query.get(_id)
            else:
                rv = self._model.query.all()
        except:
            logging.error('%s.%s() failed' % (self.__class__.__name__, '_get'), exc_info = True)
            raise
        logging.debug('Get = %s' % rv)
        return rv

    def get(self, _id = None):
        logging.info('%s.%s(%s)' % (self.__class__.__name__, 'get', _id))
        rv = self._get(_id)
        logging.info('%s.%s() = %s' % (self.__class__.__name__, 'get', rv))
        if rv:
            return {self.table: rv}, 200
        else:
            return '', 404

    def put(self, _id = None):
        logging.info('%s.%s(%s, %s)' % (self.__class__.__name__, 'put', _id, request.json))
        if not _id:
            return 'Please specify ID', 405
        try:
            #~ logging.debug('%s.%s values = %s' % (self.__class__.__name__, 'put', values))
            logging.debug('ID: %s' % _id)
            existing_entry = self._get(_id)
            logging.debug('ID: %s' % _id)
            if existing_entry:
                print('!!!!!!!!!!!!!!!!Object exists')
                for col in self.cols:
                    value = request.json.get(col, None)
                    if value:
                        setattr(existing_entry, col, value)
                rc = 201
            else:
                logging.debug('ID: %s' % _id)
                values = {}
                for col in self.cols:
                    values[col] = request.json.get(col, '')
                values['id'] = _id
                logging.debug('Values: %s' % values)
                new_entry = self._model(**values)
                db.session.add(new_entry)
                rc = 200
            db.session.flush()
            db.session.commit()
        except:
            logging.error('%s.%s() failed' % (self.__class__.__name__, 'put'), exc_info = True)
            raise
        return '',rc

    def delete(self, _id):
        logging.info('%s.%s(%s)' % (self.__class__.__name__, 'delete', _id))
        if not self._check_entry([_id,]):
            return '', 404
        try:
            del_entry = self.get(id)
            db.session.delete(del_entry)
            db.session.commit()
        except:
            logging.error('%s.%s() failed' % (self.__class__.__name__, 'delete'), exc_info = True)
            raise

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
