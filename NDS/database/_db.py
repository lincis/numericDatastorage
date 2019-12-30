from flask_sqlalchemy import SQLAlchemy, Model
from sqlalchemy import inspect
from datetime import datetime
from decimal import Decimal

class RestModel(Model):
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

db = SQLAlchemy(model_class = RestModel)
