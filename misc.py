from ObsDataRest import User

from sqlalchemy import inspect
mapper = inspect(User)
for column in mapper.attrs:
    print (column.key)
