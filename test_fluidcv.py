import fluidcv
from fluidcv import gae_fluidinfo as fluid
import unittest
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import urlfetch_stub

class FluidCVTestCase(unittest.TestCase):

    def setUp(self):
        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
        apiproxy_stub_map.apiproxy.RegisterStub(
                'urlfetch', urlfetch_stub.URLFetchServiceStub())

        fluidcv.app.config['TESTING'] = True
        self.app = fluidcv.app.test_client()
        self.USERNAME = 'fluidcv'
        self.PASSWORD = fluidcv.app.config['FLUIDCV_PASSWORD']

    def tearDown(self):
        pass

    def testNonExistentCVReturnsNotFound(self):
        rv = self.app.get('/fluidcv')
        self.assertEqual(404, rv.status_code)

    def testNameRequiredForCV(self):
        fluid.login(self.USERNAME, self.PASSWORD)
        fluid.post('/values', body={'queries': [
            ['fluiddb/users/username == "fluidcv"', 
                {
                    'fluidcv/given-name' : {
                        'value' : 'Sigmund'
                        },
                    'fluidcv/family-name' : {
                        'value' : 'Freud'
                        }
                    }
                ]
            ]})
        fluid.logout()

        rv = self.app.get('/fluidcv')
        self.assertEqual(200, rv.status_code)
        self.assertIn('Sigmund Freud', rv.data)


if __name__ == '__main__':
    unittest.main()
