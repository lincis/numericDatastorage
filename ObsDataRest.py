from db import conn, cursor

from flask import Flask, request, jsonify
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

class  DataSources(Resource):
    def get(self):
        query = cursor.execute('select * from DataSources')
        return{'DataSources':  [i[0] for i in query.fetchall()]}

    def post(self):
        print(request.json)
        id = request.json['DataSourceID']
        name = request.json['Name']
        desc = request.json['Description']
        cursor.execute('insert into DataSources values (?,?,?)',(id, name, desc))
        conn.commit()
        
api.add_resource(DataSources, '/sources') 
