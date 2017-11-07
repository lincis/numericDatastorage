import configparser
import os
from .db import get_conn

from flask import Flask, request, g
from flask_restful import Resource, Api, reqparse
import logging
from datetime import datetime
from dateutil import parser

app = Flask(__name__)
api = Api(app)

mypath = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(os.path.join(mypath,'ObsDataRest.cfg'))

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
    filename = '%s.log' % __name__,
    level=logging.DEBUG,
    format='%(asctime)s %(message)s',
)

class _ODRBase(Resource):
    def __init__(self):
        logging.debug('%s.__init__()' % self.__class__.__name__)
        self.conn, self.cursor = get_conn(getattr(g, 'db_file', db_file))
        self.table = self.__class__.__name__
        self.id_name = self.table[:-1] + 'ID'
        self.q_get_id = 'select * from %s where %s = ?' % (self.table, self.id_name)
        logging.debug('q_get_id: %s' % self.q_get_id)
        self.q_get_all = 'select * from %s' % self.table
        logging.debug('q_get_all: %s' % self.q_get_all)
        query = self.cursor.execute('PRAGMA table_info (%s)' % (self.table,))
        struct = query.fetchall()
        self.cols = []
        for col in struct:
            self.cols.append(col['name'])
        self.q_put_new = 'insert into %s values (%s)' % (self.table, ','.join(['?' for i in range(len(self.cols))]))
        logging.debug('q_put_new: %s' % self.q_put_new)
        self.q_put_update = 'update %s set %s where %s = ?' % (
            self.table,
            ' = ?,'.join(self.cols) + ' = ?',
            self.id_name
        )
        logging.debug('q_put_update: %s' % self.q_put_update)
        self.q_delete = 'delete from %s where %s = ?' % (self.table, self.id_name)
        logging.debug('q_delete: %s' % self.q_delete)
        self.q_check = 'select %s from %s where %s = ?' % (self.id_name, self.table, self.id_name)
        super(_ODRBase, self).__init__()

    def _check_entry(self,_id):
        rv = self.cursor.execute(self.q_check, _id).fetchone()
        logging.debug('%s.%s(%s) query = %s: %s' % (self.__class__.__name__, '_check_entry', _id, self.q_check, rv))
        return rv

    def get(self, _id = None):
        logging.info('%s.%s(%s)' % (self.__class__.__name__, 'get', _id))
        try:
            if _id:
                if not isinstance(_id, list):
                    _id = [_id,]
                query = self.cursor.execute(self.q_get_id, _id)
                rv = query.fetchall()
            else:
                query = self.cursor.execute(self.q_get_all)
                rv = query.fetchall()
            logging.info('%s.%s() = %s' % (self.__class__.__name__, 'get', rv))
        except:
            logging.error('%s.%s() failed' % (self.__class__.__name__, 'get'), exc_info = True)
            raise
        if rv:
            return{self.table: rv}
        else:
            return '',404

    def put(self, _id = None):
        logging.info('%s.%s(%s, %s)' % (self.__class__.__name__, 'put', _id, request.json))
        if not _id:
            return 'Please specify %s' % self.id_name, 405
        try:
            values = []
            for col in self.cols:
                if col == self.id_name:
                    continue
                values.append(request.json.get(col,''))
            values.insert(0,_id)
            #~ logging.debug('%s.%s values = %s' % (self.__class__.__name__, 'put', values))
            if self._check_entry([_id,]):
                values.append(_id)
                self.cursor.execute(self.q_put_update, values)
                rc = 201
            else:
                self.cursor.execute(self.q_put_new, values)
                rc = 200
            self.conn.commit()
        except:
            logging.error('%s.%s() failed' % (self.__class__.__name__, 'put'), exc_info = True)
            raise
        return '',rc

    def delete(self, _id):
        logging.info('%s.%s(%s)' % (self.__class__.__name__, 'delete', _id))
        if not self._check_entry([_id,]):
            return '', 404
        try:
            self.cursor.execute(self.q_delete,[_id,])
            self.conn.commit()
        except:
            logging.error('%s.%s() failed' % (self.__class__.__name__, 'delete'), exc_info = True)
            raise

class  DataSources(_ODRBase):
    pass

class DataTypes(_ODRBase):
    pass

class Data(_ODRBase):

    def __init__(self):
        super(Data, self).__init__()
        self.data_sources = DataSources()
        self.data_types = DataTypes()
        self._parse_args()
        self.id_names = ['DataTypeID', 'DataSourceID', 'DateTime']
        self.parents = {'names': [], 'values': []}
        for id in self.id_names:
            if getattr(self, id, None):
                self.parents['values'].append(getattr(self, id))
                self.parents['names'].append(id)
        self.q_check = 'select %s from %s where %s = ? and %s = ? and %s = ?' % ('Value', self.table, *self.id_names)
        self.q_get_id = 'select * from %s where %s %s' % (self.table, ' = ? and '.join(self.parents['names']), '= ?')

    def _parse_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument('DataSourceID', type=str)
        parser.add_argument('DataTypeID', type=str)
        args = parser.parse_args()
        self.DataSourceID = args.get('DataSourceID', None)
        self.DataTypeID = args.get('DataTypeID', None)

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
        return super(Data, self).get(self.parents['values'])

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
