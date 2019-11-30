from flask_sqlalchemy import SQLAlchemy, Model
from werkzeug.security import generate_password_hash, check_password_hash

class DbModel(Model):
    def insert(self, commit = True):
        db.session.add(self)
        if commit:
            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise

    def update(self):
        db.session.flush()
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

    @classmethod
    def get(cls, _id):
        if _id:
            return cls.query.get(_id)
        else:
            return cls.query.all()

    @classmethod
    def columns(cls):
        cols = []
        mapper = inspect(cls)
        for column in mapper.attrs:
            cols.append(column.key)
        return cols

    def to_dict(self, _cols):
        val_dict = {}
        for col in _cols:
            value = self.__getattribute__(col)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = float(value)
            val_dict[col] = value
        return val_dict

    @classmethod
    def from_dict(cls, _dict):
        try:
            return cls(**_dict)
        except:
            mapper = inspect(cls)
            values = {}
            mapper = inspect(cls)
            for column in mapper.attrs:
                values[column] = _dict.get(column, None)
            return cls(**values)

    @classmethod
    def delete(cls, _id):
        obj = cls.query.get(_id)
        if not obj:
            return False
        db.session.delete(obj)
        db.session.commit()
        return True

db = SQLAlchemy(model_class = DbModel)

class UserModel(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password = db.Column(db.String(120), nullable = False)

    def __repr__(self):
        return '<User %r>' % self.username

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username = username).first()


class DataTypesModel(db.Model):
    __tablename__ = 'datatypes'
    id = db.Column(db.String(40), primary_key = True, nullable = False)
    name = db.Column(db.String(255), nullable = False)
    description = db.Column(db.Text())
    units = db.Column(db.String(255))

    def __repr__(self):
        return '<Data type %r (%r)>' % (self.name, self.id)

class DataSourcesModel(db.Model):
    __tablename__ = 'datasources'
    id = db.Column(db.String(40), primary_key = True, nullable = False)
    name = db.Column(db.String(255), nullable = False)
    description = db.Column(db.Text())

    def __repr__(self):
        return '<Data source %r (%r)>' % (self.name, self.id)

class DataModel(db.Model):
    __tablename__ = 'data'
    data_type_id = db.Column(db.String(40), db.ForeignKey('datatypes.id'), primary_key = True, nullable = False)
    data_source_id = db.Column(db.String(40), db.ForeignKey('datasources.id'), primary_key = True, nullable = False)
    entity_created = db.Column(db.DateTime(), primary_key = True, nullable = False)
    value = db.Column(db.Numeric())
    def __repr__(self):
        return '<Data entry %r>' % self.value
