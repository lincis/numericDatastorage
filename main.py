from gevent import monkey
monkey.patch_all()

from ObsDataRest import app, socketio, db, UserModel, DataModel, DataTypesModel, DataSourcesModel
from sqlalchemy.exc import IntegrityError
import os
import subprocess

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        try:
            user = UserModel(username = os.environ.get('API_USER'))
            user.set_password(os.environ.get('API_PW'))
            user.insert()
        except IntegrityError:
            print("Default user already exists")
            pass
    try:
        subprocess.run(["service redis-server start"])
    except:
        print("Could not start redis")
    socketio.run(app, debug = True, host = '0.0.0.0')
