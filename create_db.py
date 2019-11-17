from ObsDataRest import app, db, UserModel, DataModel, DataTypesModel, DataSourcesModel
from sqlalchemy.exc import IntegrityError
import os

with app.app_context():
    db.create_all()
    try:
        user = UserModel(username = os.environ.get('API_USER'))
        user.set_password(os.environ.get('API_PW'))
        user.insert()
    except IntegrityError:
        print("Default user already exists")
        pass
