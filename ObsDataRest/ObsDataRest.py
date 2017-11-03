from .db import get_conn

from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import logging

conn, cursor = get_conn()

logging.basicConfig(
    filename = '%s.log' % __name__,
    level=logging.DEBUG,
    format='%(asctime)s %(message)s',
)

app = Flask(__name__)
api = Api(app)

class  DataSources(Resource):
    def get(self, source_id = None):
        logging.info("%s.%s(%s)" % (self.__class__.__name__, "get", source_id))
        try:
            if source_id:
                query = cursor.execute('select * from DataSources where DataSourceID = ?', (source_id,))
                rv = query.fetchone()
            else:
                query = cursor.execute('select * from DataSources')
                rv = query.fetchall()
            logging.info("%s.%s() = %s" % (self.__class__.__name__, "get", rv))
            return{'DataSources': rv}
        except:
            logging.error("%s.%s() failed" % (self.__class__.__name__, "get"), exc_info = True)
            raise

    def post(self, source_id):
        logging.info("%s.%s(%s, %s)" % (self.__class__.__name__, "post", source_id, request.json))
        try:
            name = request.json['Name']
            desc = request.json['Description']
            cursor.execute('insert into DataSources values (?,?,?)',(source_id, name, desc))
            conn.commit()
        except:
            logging.error("%s.%s() failed" % (self.__class__.__name__, "post"), exc_info = True)
            raise

    def delete(self, source_id):
        logging.info("%s.%s(%s)" % (self.__class__.__name__, "delete", source_id))
        try:
            cursor.execute('delete from DataSources where DataSourceID = ?',(source_id,))
            conn.commit()
        except:
            logging.error("%s.%s() failed" % (self.__class__.__name__, "delete"), exc_info = True)
            raise

api.add_resource(DataSources,
        '/sources/<source_id>',
        '/sources/'
    )
