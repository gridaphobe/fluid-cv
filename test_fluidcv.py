import fluidcv
import gae_fluidinfo as fluid
import sys
import unittest
import uuid
from fluidcv.models import Person, Education, Work, OReillySkill
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import urlfetch_stub

apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
apiproxy_stub_map.apiproxy.RegisterStub(
        'urlfetch', urlfetch_stub.URLFetchServiceStub())

fluidcv.app.config['TESTING'] = True
USERNAME = 'test'
PASSWORD = 'test'

class FluidCVTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        fluid.login(USERNAME, PASSWORD)
        # create necessary tags
        for cls in [Person, Education, Work]:
            for tag in cls.TAGS:
                resp = fluid.post('/tags/test', body={'name' : tag,
                                                      'description' : None,
                                                      'indexed' : True})
                if resp.status_code not in [201, 412]:
                    print 'Failed to create tag: %s' % tag
                    print resp.headers
                    sys.exit(1)
        fluid.logout()

    @classmethod
    def tearDownClass(cls):
        fluid.login(USERNAME, PASSWORD)
        # create necessary tags
        for cls in [Person, Education, Work]:
            for tag in cls.TAGS:
                fluid.delete('/tags/test/%s' % tag)
        fluid.logout()

    def setUp(self):
        self.app = fluidcv.app.test_client()

    def tearDown(self):
        pass

    def testNonExistentCVReturnsNotFound(self):
        rv = self.app.get('/%s' % uuid.uuid4())
        self.assertEqual(404, rv.status_code)

    def testNameRequiredForCV(self):
        fluid.login(USERNAME, PASSWORD)
        resp = fluid.put('/values', body={'queries': [
            ['fluiddb/users/username = "test"',
                {
                    'test/given-name' : {
                        'value' : 'Sigmund'
                        },
                    'test/family-name' : {
                        'value' : 'Freud'
                        }
                    }
                ]
            ]})


        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertIn('Sigmund Freud', rv.data)

        # now cleanup
        fluid.delete('/delete', query='fluiddb/users/username = "test"',
                                tags=['test/given-name', 'test/family-name'])
        fluid.logout()


if __name__ == '__main__':
    unittest.main()
