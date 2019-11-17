import json
import pytest
import uuid
import random
from dateutil import parser
from datetime import timedelta
from ObsDataRest import app, db, add_user
import math
source_id = str(uuid.uuid4())
type_id = str(uuid.uuid4())

src_1 = 'SRC:1'
src_2 = 'SRC:2'
type_1 = 'TYPE:1'
type_2 = 'TYPE:2'

n = 5

@pytest.fixture(autouse = True, scope = 'session')
def token():
    global token_value
    with app.app_context():
        db.create_all()
        with app.test_client() as client:
            add_user('Username', 'Password')
            r = client.post('/authorize',
                data = json.dumps({'username': 'Username', 'password': 'Password'})
                , content_type = 'application/json'
            )
            data = json.loads(r.data.decode('utf-8'))
            token_value = data.get('access_token', 'none')
            yield data.get('access_token', 'none')

def header(token):
    return {'Authorization': 'Bearer %s' % token}

def random_datetime(start, max_diff):
    diff = timedelta(days = random.randint(0, max_diff), seconds = random.randint(0, 86399))
    return (parser.parse(start) + diff).isoformat()

class TestDataSources:
    def setup_class(self):
        app.testing = True
        self.client = app.test_client()

    @pytest.mark.last
    @pytest.mark.parametrize('path,_id',[('sources', source_id), ('types', type_id)])
    def test_delete(self, path, _id, token):
        r = self.client.delete('/%s/%s' % (path, _id), headers = header(token))
        assert r.status_code == 200

    @pytest.mark.first
    @pytest.mark.parametrize('code',(200,201))
    def test_source_post(self, code, token):
        r = self.client.put(
            '/sources/%s' % (source_id),
            data = json.dumps({ 'name': 'Test', 'description': 'Test description' }),
            content_type = 'application/json',
            headers = header(token)
        )
        assert r.status_code == code

    @pytest.mark.parametrize('_id',('',source_id, 'False'))
    def test_source_get(self, _id):
        r = self.client.get('/sources/%s' % (_id),
            content_type = 'application/json')
        if _id == 'False':
            assert r.status_code == 404
            return
        print(json.loads(r.data.decode('utf-8')))
        r_data = json.loads(r.data.decode('utf-8'))['DataSources'].pop()
        assert r.status_code == 200
        assert r_data['id'] == source_id

    @pytest.mark.first
    @pytest.mark.parametrize('code',(200,201,405))
    def test_type_post(self, code, token):
        r = self.client.put('/types/%s' % (type_id if code < 400 else ''),
            data = json.dumps({ 'name': 'Test', 'description': 'Test description', 'units': 'Test units' }),
            content_type = 'application/json',
            headers = header(token)
        )
        assert r.status_code == code

    @pytest.mark.parametrize('_id',('',type_id, 'False'))
    def test_type_get(self, _id):
        r = self.client.get('/types/%s' % (_id),
            content_type = 'application/json')
        if _id == 'False':
            assert r.status_code == 404
            return
        r_data = json.loads(r.data.decode('utf-8'))['DataTypes'].pop()
        assert r.status_code == 200
        assert r_data['id'] == type_id

class TestData:
    def setup_class(self):
        app.testing = True
        self.client = app.test_client()
        self.client.put('/sources/%s' % (src_1),
            data = json.dumps({ 'name': 'Test 1', 'description': 'Test source 1' }),
            headers = header(token_value),
            content_type = 'application/json')
        self.client.put('/sources/%s' % (src_2),
            data = json.dumps({ 'name': 'Test 2', 'description': 'Test source 2' }),
            headers = header(token_value),
            content_type = 'application/json')
        self.client.put('/types/%s' % (type_1),
            data = json.dumps({ 'name': 'Test 1', 'description': 'Test type 1', 'units': 'unit1' }),
            headers = header(token_value),
            content_type = 'application/json')
        self.client.put('/types/%s' % (type_2),
            data = json.dumps({ 'name': 'Test 2', 'description': 'Test type 2', 'units': 'unit2' }),
            headers = header(token_value),
            content_type = 'application/json')

    @pytest.mark.parametrize('src', (src_1, src_2, '', 'Junk'))
    @pytest.mark.parametrize('typ', (type_1, type_2, '', 'Junk'))
    def test_data_put(self, src, typ, token):
        r = self.client.put('/data',
            data = json.dumps({'Data': [{ 'value': 25.5, 'data_type_id': typ, 'data_source_id': src },]}),
            content_type = 'application/json',
            headers = header(token)
        )
        if 'Junk' in [src, typ] or not (src and typ):
            rc = 400
        else:
            rc = 200
        assert r.status_code == rc

    @pytest.mark.parametrize('src', (src_1, src_2, '', 'Junk'))
    @pytest.mark.parametrize('typ', (type_1, type_2, '', 'Junk'))
    def test_data_put_bulk(self, src, typ, token):
        payload = []
        for o in zip([random_datetime('2017-01-01T00:00', 365) for i in range(n)], [random.uniform(1,100) for i in range(n)]):
            payload.append({'data_type_id': typ, 'data_source_id': src, 'entity_created': o[0], 'value': o[1]})
        r = self.client.put('/data', data = json.dumps({'Data': payload}), content_type = 'application/json',
            headers = header(token)
        )
        if 'Junk' in [src,typ] or not (src and typ):
            rc = 400
        else:
            rc = 200
        assert r.status_code == rc

    @pytest.mark.parametrize('src', (src_1, src_2, '', 'Junk'))
    @pytest.mark.parametrize('typ', (type_1, type_2, '', 'Junk'))
    @pytest.mark.last
    def test_dates(self, src, typ):
        r = self.client.get('/data/dates/%s/%s' % (src, typ))
        if not (src and typ):
            assert r.status_code == 404
            return
        assert r.status_code == 200
        r_data = json.loads(r.data.decode('utf-8'))
        if 'Junk' in [src, typ]:
            assert r_data.get('max_date') == None
            assert r_data.get('min_date') == None
        else:
            assert r_data.get('max_date')
            assert r_data.get('min_date')

    @pytest.mark.parametrize('src', (src_1, src_2, '', 'Junk'))
    @pytest.mark.parametrize('typ', (type_1, type_2, '', 'Junk'))
    @pytest.mark.last
    def test_data_get(self, src, typ):
        r = self.client.get('/data/%s/%s' % (src, typ))
        if 'Junk' in [src, typ] or not (src and typ):
            assert r.status_code == 404
            return
        assert r.status_code == 200
        data = json.loads(r.data.decode('utf-8'))['Data']
        assert len(data)

    @pytest.mark.parametrize('src', (src_1, src_2))
    @pytest.mark.parametrize('typ', (type_1, type_2))
    @pytest.mark.parametrize('start_date', ('2016-01-01', '2019-01-01', '2999-01-01', ''))
    @pytest.mark.parametrize('end_date', ('2016-01-01', '2019-01-01', '2999-01-01', ''))
    @pytest.mark.last
    def test_data_get_by_date(self, src, typ, start_date, end_date):
        r = self.client.get('/data/%s/%s/%s/%s' % (src, typ, end_date, start_date))
        # print(json.loads(r.data.decode('utf-8')))
        if start_date == end_date or not (start_date and end_date) or start_date == '2999-01-01' or end_date == '2016-01-01':
            assert r.status_code == 404
            return
        assert r.status_code == 200
        data = json.loads(r.data.decode('utf-8'))['Data']
        dt_start_date = parser.parse(start_date)
        dt_end_date = parser.parse(end_date)
        if dt_start_date < parser.parse('2019-01-01'):
            if dt_end_date < parser.parse('2999-01-01'):
                assert len(data) == n
            else:
                assert len(data) == n + 1
        else:
            assert len(data) == 1
            assert math.isclose(data[0]['value'], 25.5)

    @pytest.mark.parametrize('src', (src_1, src_2))
    @pytest.mark.parametrize('typ', (type_1, type_2))
    @pytest.mark.parametrize('end_date', ('2016-01-01', '2019-01-01', '2999-01-01'))
    @pytest.mark.last
    def test_data_get_by_end_date(self, src, typ, end_date):
        r = self.client.get('/data/%s/%s/%s' % (src, typ, end_date))
        # print(json.loads(r.data.decode('utf-8')))
        if end_date == '2016-01-01':
            assert r.status_code == 404
            return
        assert r.status_code == 200
        data = json.loads(r.data.decode('utf-8'))['Data']
        dt_end_date = parser.parse(end_date)
        if dt_end_date < parser.parse('2999-01-01'):
            assert len(data) == n
        else:
            assert len(data) == n + 1

# class TestAccess:
#     def setup_class(self):
#         app.testing = True
#         self.client = app.test_client()
#
#     @pytest.mark.parametrize('mode',('read','write'))
#     def test_access(self, mode):
#         app.config['network_%s' % mode] = '192.0.0.0/24'
#         if mode == 'read':
#             r = self.client.get('/data/')
#         else:
#             r = self.client.delete('/data/')
#         assert r.status_code == 403
#         app.config['network_%s' % mode] = None
