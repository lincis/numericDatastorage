import pytest
import requests
import uuid
source_id = str(uuid.uuid4())

class TestDataSources:
    def setup_class(self):
        self.urlbase = 'http://127.0.0.1:5000/sources/'

    def teardown_class(self):
        r = requests.delete('%s%s' % (self.urlbase, source_id))
        assert r.status_code == 200

    @pytest.mark.parametrize('resp_code',(200,500))
    def test_source_post(self, resp_code):
        r = requests.post('%s%s' % (self.urlbase, source_id),
            json={ 'Name': 'Test', 'Description': 'Test description' })
        assert r.status_code == resp_code
