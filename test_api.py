import json
import pytest
import uuid
import sqlite3
import random
from dateutil import parser
from datetime import timedelta
from time import mktime
from ObsDataRest import app, init_db
source_id = str(uuid.uuid4())
type_id = str(uuid.uuid4())

src_1 = 'SRC:1'
src_2 = 'SRC:2'
type_1 = 'TYPE:1'
type_2 = 'TYPE:2'


@pytest.fixture(autouse = True, scope = "session")
def db():
    with app.app_context():
        init_db('./.test.db')

def random_datetime(start, max_diff):
    diff = timedelta(days = random.randint(0, max_diff), seconds = random.randint(0, 86399))
    return (parser.parse(start) + diff).isoformat()

class TestDataSources:
    def setup_class(self):
        app.testing = True
        self.client = app.test_client()

    @pytest.mark.last
    @pytest.mark.parametrize('path,_id',[('sources', source_id), ('types', type_id)])
    def test_delete(self, path, _id):
        r = self.client.delete('/%s/%s' % (path, _id))
        assert r.status_code == 200

    @pytest.mark.first
    @pytest.mark.parametrize('code',(200,201))
    def test_source_post(self, code):
        r = self.client.put('/sources/%s' % (source_id),
            data=json.dumps({ 'Name': 'Test', 'Description': 'Test description' }),
            content_type='application/json')
        assert r.status_code == code

    @pytest.mark.parametrize('id',('',source_id, 'False'))
    def test_source_get(self, id):
        r = self.client.get('/sources/%s' % (id),
            content_type='application/json')
        if id == 'False':
            assert r.status_code == 404
            return
        r_data = json.loads(r.data)['DataSources'].pop()
        assert r.status_code == 200
        assert r_data['DataSourceID'] == source_id

    @pytest.mark.first
    @pytest.mark.parametrize('code',(200,201,405))
    def test_type_post(self, code):
        r = self.client.put('/types/%s' % (type_id if code < 400 else ''),
            data=json.dumps({ 'Name': 'Test', 'Description': 'Test description', 'Units': 'Test units' }),
            content_type='application/json')
        assert r.status_code == code

    @pytest.mark.parametrize('id',('',type_id, 'False'))
    def test_type_get(self, id):
        r = self.client.get('/types/%s' % (id),
            content_type='application/json')
        if id == 'False':
            assert r.status_code == 404
            return
        r_data = json.loads(r.data)['DataTypes'].pop()
        assert r.status_code == 200
        assert r_data['DataTypeID'] == type_id

class TestData:
    def setup_class(self):
        app.testing = True
        self.client = app.test_client()
        r = self.client.put('/sources/%s' % (src_1),
            data=json.dumps({ 'Name': 'Test 1', 'Description': 'Test source 1' }),
            content_type='application/json')
        r = self.client.put('/sources/%s' % (src_2),
            data=json.dumps({ 'Name': 'Test 2', 'Description': 'Test source 2' }),
            content_type='application/json')
        r = self.client.put('/types/%s' % (type_1),
            data=json.dumps({ 'Name': 'Test 1', 'Description': 'Test type 1', 'Units': 'unit1' }),
            content_type='application/json')
        r = self.client.put('/types/%s' % (type_2),
            data=json.dumps({ 'Name': 'Test 2', 'Description': 'Test type 2', 'Units': 'unit2' }),
            content_type='application/json')

    @pytest.mark.parametrize('src', (src_1, src_2, '', 'Junk'))
    @pytest.mark.parametrize('typ', (type_1, type_2, '', 'Junk'))
    def test_data_put(self, src, typ):
        r = self.client.put('/data/?DataSourceID=%s&DataTypeID=%s' % (src, typ),
            data=json.dumps({ 'Value': 25.5 }),
            content_type='application/json')
        if not (src and typ):
            rc = 400
        elif 'Junk' in [src,typ]:
            rc = 400
        else:
            rc = 200
        assert r.status_code == rc

    @pytest.mark.parametrize('src', (src_1, src_2, '', 'Junk'))
    @pytest.mark.parametrize('typ', (type_1, type_2, '', 'Junk'))
    def test_data_put_bulk(self, src, typ):
        r = self.client.put('/data/?DataSourceID=%s&DataTypeID=%s' % (src, typ),
            data=json.dumps({
                'DateTime': [random_datetime('2017-01-01T00:00', 365) for i in range(3)],
                'Value': [random.uniform(1,100) for i in range(3)],
            }),
            content_type='application/json')
        if not (src and typ):
            rc = 400
        elif 'Junk' in [src,typ]:
            rc = 400
        else:
            rc = 200
        assert r.status_code == rc

    @pytest.mark.parametrize('src', (src_1, src_2, '', 'Junk'))
    @pytest.mark.parametrize('typ', (type_1, type_2, '', 'Junk'))
    def test_data_get(self, src, typ):
        r = self.client.get('/data/?DataSourceID=%s&DataTypeID=%s' % (src, typ))
        if 'Junk' in [src, typ]:
            assert r.status_code == 404
        else:
            assert r.status_code == 200
            data = json.loads(r.data)['Data']
            mult = []
            for var in ['src', 'typ']:
                val = locals().get(var, None)
                if val:
                    mult.append(2)
                else:
                    mult.append(4)
            assert len(data) == mult[0] * mult[1]
