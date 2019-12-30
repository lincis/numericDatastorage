from ._model import UserModel, DataTypesModel, DataSourcesModel, DataModel

def add_user(username, password):
    user = UserModel(username = username)
    user.set_password(password)
    user.insert()
