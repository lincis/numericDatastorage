from ObsDataRest import app, db, UserModel, DataModel, DataTypesModel, DataSourcesModel
import os

if __name__ == '__main__':
    app.run(host = '0.0.0.0')
