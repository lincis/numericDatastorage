import configparser
import os
from .db import get_conn

from flask import Flask, request, jsonify, g
from flask_restful import Resource, Api
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
        super(_ODRBase, self).__init__()

    def _check_entry(self,id):
        query = 'select %s from %s where %s = ?' % (self.id_name, self.table, self.id_name)
        rv = self.cursor.execute(query, [id,]).fetchone()
        logging.debug('%s.%s(%s) query = %s: %s' % (self.__class__.__name__, '_check_entry', id, query, rv))
        return rv

    def get(self, id = None):
        logging.info('%s.%s(%s)' % (self.__class__.__name__, 'get', id))
        try:
            if id:
                query = self.cursor.execute(self.q_get_id, [id,])
                rv = query.fetchone()
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

    def put(self, id = None):
        logging.info('%s.%s(%s, %s)' % (self.__class__.__name__, 'put', id, request.json))
        if not id:
            return 'Please specify %s' % self.id_name, 405
        try:
            values = []
            for col in self.cols:
                if col == self.id_name:
                    continue
                values.append(request.json.get(col,''))
            values.insert(0,id)
            #~ logging.debug('%s.%s values = %s' % (self.__class__.__name__, 'put', values))
            if self._check_entry(id):
                values.append(id)
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

    def delete(self, id):
        logging.info('%s.%s(%s)' % (self.__class__.__name__, 'delete', id))
        if not self._check_entry(id):
            return '', 404
        try:
            self.cursor.execute(self.q_delete,[id,])
            self.conn.commit()
        except:
            logging.error('%s.%s() failed' % (self.__class__.__name__, 'delete'), exc_info = True)
            raise

class  DataSources(_ODRBase):
    pass

class DataTypes(_ODRBase):
    pass

class Data(_ODRBase):

    def _check_entry(self, type_id, source_id):
        query = 'select %s from %s where %s = ? and %s = ?' % (self.type_id, self.table, 'DataTypeID', 'DataSourceID')
        rv = self.cursor.execute(query, [type_id,source_id,]).fetchone()
        logging.debug('%s.%s(%s) query = %s: %s' % (self.__class__.__name__, '_check_entry', id, query, rv))
        return rv
        

    def put(self):
        logging.info('%s.%s(%s, %s)' % (self.__class__.__name__, 'put', id, request.json))
        type_id = request.json.get('DataTypeID', None)
        source_id = request.json.get('DataSourceID', None)
        time = request.json.get('ObsTime', None)
        if not (type_id and source_id):
            return 'Please specify data source and type'
        if not time:
            time = datetime.now()
        else:
            try:
                time = parser.parse(time)
            except:
                logging.error('Cannot parese time', exc_info = True)
                return 'Cannot parse provided date/time',400

api.add_resource(DataSources,
        '/sources/<id>',
        '/sources/'
    )
api.add_resource(DataTypes,
        '/types/<id>',
        '/types/'
    )
api.add_resource(Data,
        '/data/',
    )
