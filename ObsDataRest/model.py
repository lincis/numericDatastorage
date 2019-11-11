from flask_sqlalchemy import SQLAlchemy
from . import app

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password = db.Column(db.String(120), unique = True, nullable = False)

    def __repr__(self):
        return '<User %r>' % self.username

class DataTypes(db.Model):
    id = db.Column(db.String(36), primary_key = True, nullable = False)
    name = db.Column(db.String(255), nullable = False)
    description = db.Column(db.Text())
    units = db.Column(db.String(255))

    def __repr__(self):
        return '<Data type %r>' % self.name

class DataSources(db.Model):
    id = db.Column(db.String(36), primary_key = True, nullable = False)
    name = db.Column(db.String(255), nullable = False)
    description = db.Column(db.Text())

    def __repr__(self):
        return '<Data source %r>' % self.name

class Data(db.Model):
    data_type_id = db.Column(db.String(36), db.ForeignKey('datatypes.id'), primary_key = True, nullable = False)
    data_source_id = db.Column(db.String(36), db.ForeignKey('datasources.id'), primary_key = True, nullable = False)
    entity_created = db.Column(db.DateTime(), nullable = False)
    value = db.Column(db.Numeric())
    def __repr__(self):
        return '<Data entry %r>' % self.value
