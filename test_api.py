import json
import pytest
import uuid
import sqlite3
from ObsDataRest import app, init_db
source_id = str(uuid.uuid4())
type_id = str(uuid.uuid4())


class TestDataSources:
    def setup_class(self):
        with app.app_context():
            init_db('./.test.db')
        app.testing = True
        self.client = app.test_client()

    def teardown_class(self):
        r = self.client.delete('/sources/%s' % (source_id))
        assert r.status_code == 200
        r = self.client.delete('/types/%s' % (type_id))
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
        data = r_data = json.loads(r.data)['DataSources']
        if not id:
            r_data = data.pop()
        assert r.status_code == 200
        assert r_data['DataSourceID'] == source_id

    @pytest.mark.first
    @pytest.mark.parametrize('code',(200,201))
    def test_type_post(self, code):
        r = self.client.put('/types/%s' % (type_id),
            data=json.dumps({ 'Name': 'Test', 'Description': 'Test description', 'Units': 'Test units' }),
            content_type='application/json')
        assert r.status_code == code

    def test_type_post3(self):
        r = self.client.put('/types/',
            data=json.dumps({ 'Name': 'Test', 'Description': 'Test description', 'Units': 'Test units' }),
            content_type='application/json')
        assert r.status_code == 405

    @pytest.mark.parametrize('id',('',type_id, 'False'))
    def test_type_get(self, id):
        r = self.client.get('/types/%s' % (id),
            content_type='application/json')
        if id == 'False':
            assert r.status_code == 404
            return
        data = r_data = json.loads(r.data)['DataTypes']
        if not id:
            r_data = data.pop()
        assert r.status_code == 200
        assert r_data['DataTypeID'] == type_id
