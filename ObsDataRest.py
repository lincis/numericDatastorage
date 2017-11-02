from db import conn, cursor

from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import logging

logging.basicConfig(
    filename = '%s.log' % __name__,
    level=logging.DEBUG,
    format='%(asctime)s %(message)s',
)

app = Flask(__name__)
api = Api(app)

class  DataSources(Resource):
    def get(self):
        logging.info("%s.%s()" % (self.__class__.__name__, "get"))
        try:
            query = cursor.execute('select * from DataSources')
            rv = query.fetchall()
            logging.info("%s.%s() = %s" % (self.__class__.__name__, "get", rv))
            return{'DataSources': rv}
        except:
            logging.error("%s.%s() failed" % (self.__class__.__name__, "get"), exc_info = True)
            raise

    def post(self):
        logging.info("%s.%s(%s)" % (self.__class__.__name__, "post", request.json))
        try:
            id = request.json['DataSourceID']
            name = request.json['Name']
            desc = request.json['Description']
            cursor.execute('insert into DataSources values (?,?,?)',(id, name, desc))
            conn.commit()
        except:
            logging.error("%s.%s() failed" % (self.__class__.__name__, "post"), exc_info = True)
            raise

api.add_resource(DataSources, '/sources')
