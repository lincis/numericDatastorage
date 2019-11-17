from ObsDataRest import app, db, UserModel, DataModel, DataTypesModel, DataSourcesModel
from sqlalchemy.exc import IntegrityError
import os

if __name__ == '__main__':
    app.run(host = '0.0.0.0')
