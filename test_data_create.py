# from NDS.webapp import app
# from NDS.database import db
# from NDS.model import UserModel, DataModel, DataTypesModel, DataSourcesModel
# from sqlalchemy.exc import IntegrityError
# import os
# from datetime import datetime
#
# with app.app_context():
#     db.create_all()
#     try:
#         data = DataTypesModel(id = 'type', name = 'Test name', description = 'Test description', units = 'Test units')
#         data.insert()
#     except IntegrityError:
#         print("Default type already exists")
#         pass
#     try:
#         data = DataSourcesModel(id = 'source', name = 'Test name', description = 'Test description')
#         data.insert()
#     except IntegrityError:
#         print("Default source already exists")
#         pass
#     try:
#         data = DataModel(data_type_id = 'type', data_source_id = 'source', value = 42, entity_created = datetime.now())
#         data.insert()
#     except IntegrityError:
#         print("Default data already exists")
#         pass
