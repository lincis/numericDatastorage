import eventlet
eventlet.monkey_patch()

from NDS.webapp import app, socketio
from NDS.database import db
from NDS.model import UserModel
from sqlalchemy.exc import IntegrityError
import os

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
    socketio.run(app, debug = os.environ.get('FLASK_DEBUG', False), host = '0.0.0.0')
