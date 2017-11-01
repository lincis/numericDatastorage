import requests
r = requests.post('http://127.0.0.1:5000/sources',
    json={ 'DataSourceID': 'ID:1', 'Name': 'Test', 'Description': 'Test description' })
print (r.status_code)
