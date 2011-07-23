import fluidcv
import gae_fluidinfo as fluid
import sys
import time
import unittest
from uuid import uuid4
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
        rpcs = []
        for cls in [Person, Education, Work]:
            for tag in cls.TAGS:
                rpc = fluid.post('/tags/test', async=True,
                                 body={'name' : tag,
                                       'description' : None,
                                       'indexed' : True})
                rpcs.append(rpc)
        for rpc in rpcs:
            resp = fluid.result(rpc)
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
        fluid.login(USERNAME, PASSWORD)

        
    def tearDown(self):
        fluid.logout()

        
    def testNonExistentUserReturnsNotFound(self):
        rv = self.app.get('/%s' % uuid4())
        self.assertEqual(404, rv.status_code)

        
    #########################################
    # Person Tests
    #########################################
    def testPersonWithoutNameUsesSystemTags(self):
        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertIn('test', rv.data)

        
    def testGivenNameInPerson(self):
        fluid.put('/values', body={'queries': [
                    ['fluiddb/users/username = "test"',
                     {'test/given-name' : {'value' : 'Sigmund'}}]]})
        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertIn('Sigmund', rv.data)
        fluid.delete('/values', query='fluiddb/users/username = "test"',
                     tags=['test/given-name'])


    def testFamilyNameInPerson(self):
        fluid.put('/values', body={'queries': [
                    ['fluiddb/users/username = "test"',
                     {'test/family-name' : {'value' : 'Freud'}}]]})
        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertIn('Freud', rv.data)
        fluid.delete('/values', query='fluiddb/users/username = "test"',
                     tags=['test/family-name'])

        
    def testRoleInPerson(self):
        fluid.put('/values', body={'queries': [
                    ['fluiddb/users/username = "test"',
                     {'test/role': {'value' : 'badass'}}]]})
        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertIn('badass', rv.data)
        fluid.delete('/values', query='fluiddb/users/username = "test"',
                     tags=['test/role'])

        
    def testEmailInPerson(self):
        fluid.put('/values', body={'queries': [
                    ['fluiddb/users/username = "test"',
                     {'test/email': {'value' : 'test@example.com'}}]]})
        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertIn('test@example.com', rv.data)
        fluid.delete('/values', query='fluiddb/users/username = "test"',
                     tags=['test/email'])

        
    def testCellPhoneInPerson(self):
        fluid.put('/values', body={'queries': [
                    ['fluiddb/users/username = "test"',
                     {'test/cell-phone': {'value' : '(123) 456-7890'}}]]})
        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertIn('(123) 456-7890', rv.data)
        fluid.delete('/values', query='fluiddb/users/username = "test"',
                     tags=['test/cell-phone'])


    def testStreetAddressInPerson(self):
        fluid.put('/values', body={'queries': [
                    ['fluiddb/users/username = "test"',
                     {'test/street-address': {'value' : '123 Main St.'}}]]})
        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertIn('123 Main St.', rv.data)
        fluid.delete('/values', query='fluiddb/users/username = "test"',
                     tags=['test/street-address'])
        

    def testLocalityInPerson(self):
        fluid.put('/values', body={'queries': [
                    ['fluiddb/users/username = "test"',
                     {'test/locality': {'value' : 'New York'}}]]})
        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertIn('New York', rv.data)
        fluid.delete('/values', query='fluiddb/users/username = "test"',
                     tags=['test/locality'])

        
    def testRegionInPerson(self):
        fluid.put('/values', body={'queries': [
                    ['fluiddb/users/username = "test"',
                     {'test/region': {'value' : 'NY'}}]]})
        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertIn('NY', rv.data)
        fluid.delete('/values', query='fluiddb/users/username = "test"',
                     tags=['test/region'])


    def testPostalCodeInPerson(self):
        fluid.put('/values', body={'queries': [
                    ['fluiddb/users/username = "test"',
                     {'test/postal-code': {'value' : '12345'}}]]})
        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertIn('12345', rv.data)
        fluid.delete('/values', query='fluiddb/users/username = "test"',
                     tags=['test/postal-code'])


    def testSummaryInPerson(self):
        fluid.put('/values', body={'queries': [
                    ['fluiddb/users/username = "test"',
                     {'test/summary': {'value' : 'I Rock!'}}]]})
        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertIn('I Rock!', rv.data)
        fluid.delete('/values', query='fluiddb/users/username = "test"',
                     tags=['test/summary'])
        

    #######################################
    # Work Tests
    #######################################
    def testEmployerRequiredForWork(self):
        fluid.put('/values', body={'queries': [
                    ['fluiddb/about = "fluidinfo"',
                     {'test/company': {'value': 'Fluidinfo'},
                      'test/title': {'value': 'Dictator'}}]]})
        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertNotIn('Fluidinfo', rv.data)
        self.assertNotIn('Dictator', rv.data)
        fluid.put('/about/fluidinfo/test/employer', body=None)
        # FIXME: this is really hacky
        # wait for Fluidinfo's index to update...
        time.sleep(5)
        rv = self.app.get('/test')
        self.assertEqual(200, rv.status_code)
        self.assertIn('Fluidinfo', rv.data)
        self.assertIn('Dictator', rv.data)
        fluid.delete('/values', query='fluiddb/about = "fluidinfo"',
                     tags=['test/company', 'test/title', 'test/employer'])
        

    def testWorkValidations(self):
        # title is required
        tags = {'test/company': {'value': 'Fluidinfo'},
                'test/start-date': {'value': '2010-01-01'},
                'test/end-date': {'value': '2011-01-01'},
                'test/functions': {'value': ['foo', 'bar']}}
        work = Work(uuid4(), 'test', tags)
        self.assertFalse(work.valid)
        
        # company is not required
        tags = {'test/title': {'value': 'Dictator'},
                'test/start-date': {'value': '2010-01-01'},
                'test/end-date': {'value': '2011-01-01'},
                'test/functions': {'value': ['foo', 'bar']}}
        work = Work(uuid4(), 'test', tags)
        self.assertTrue(work.valid)

        # dates are not required
        tags = {'test/title': {'value': 'Dictator'},
                'test/company': {'value': 'Fluidinfo'},
                'test/functions': {'value': ['foo', 'bar']}}
        work = Work(uuid4(), 'test', tags)
        self.assertTrue(work.valid)

        # start-date without end-date is valid
        tags = {'test/title': {'value': 'Dictator'},
                'test/company': {'value': 'Fluidinfo'},
                'test/start-date': {'value': '2010-01-01'},
                'test/functions': {'value': ['foo', 'bar']}}
        work = Work(uuid4(), 'test', tags)
        self.assertTrue(work.valid)

        # end-date without start-date is invalid
        tags = {'test/title': {'value': 'Dictator'},
                'test/company': {'value': 'Fluidinfo'},
                'test/end-date': {'value': '2010-01-01'},
                'test/functions': {'value': ['foo', 'bar']}}
        work = Work(uuid4(), 'test', tags)
        self.assertFalse(work.valid)

        # functions are not required
        tags = {'test/title': {'value': 'Dictator'},
                'test/company': {'value': 'Fluidinfo'},
                'test/start-date': {'value': '2009-01-01'},
                'test/end-date': {'value': '2010-01-01'}}
        work = Work(uuid4(), 'test', tags)
        self.assertTrue(work.valid)


    def testWorkFromResponse(self):
        tags1 = {'test/title': {'value': 'Dictator'}}
        uuid1 = uuid4()
        work1 = Work(uuid1, 'test', tags1)
        tags2 = {'test/company': {'value': 'Fluidinfo'}}
        uuid2 = uuid4()
        work2 = Work(uuid2, 'test', tags2)
        self.assertEqual([work1], Work.from_response('test', {uuid1: tags1,
                                                              uuid2: tags2}))


    #######################################
    # Education Tests
    #######################################
    def testEducationValidations(self):
        # school-name is required
        tags = {'test/school-location': {'value': 'New York, NY'},
                'test/major': {'value': 'Computer Science'},
                'test/degree': {'value': 'BS'},
                'test/start-date': {'value': '2009-01-01'},
                'test/end-date': {'value': '20101-01-01'},
                'test/gpa': {'value': 4.0}}
        school = Education(uuid4(), 'test', tags)
        self.assertFalse(school.valid)
        
        # school-location is not required
        tags = {'test/school-name': {'value': 'New York University'},
                'test/major': {'value': 'Computer Science'},
                'test/degree': {'value': 'BS'},
                'test/start-date': {'value': '2009-01-01'},
                'test/end-date': {'value': '20101-01-01'},
                'test/gpa': {'value': 4.0}}
        school = Education(uuid4(), 'test', tags)
        self.assertTrue(school.valid)
        
        # major is required
        tags = {'test/school-name': {'value': 'New York University'},
                'test/school-location': {'value': 'New York, NY'},
                'test/degree': {'value': 'BS'},
                'test/start-date': {'value': '2009-01-01'},
                'test/end-date': {'value': '20101-01-01'},
                'test/gpa': {'value': 4.0}}
        school = Education(uuid4(), 'test', tags)
        self.assertFalse(school.valid)

        # degree is required
        tags = {'test/school-name': {'value': 'New York University'},
                'test/school-location': {'value': 'New York, NY'},
                'test/major': {'value': 'Computer Science'},
                'test/start-date': {'value': '2009-01-01'},
                'test/end-date': {'value': '20101-01-01'},
                'test/gpa': {'value': 4.0}}
        school = Education(uuid4(), 'test', tags)
        self.assertFalse(school.valid)

        # dates are not required
        tags = {'test/school-name': {'value': 'New York University'},
                'test/school-location': {'value': 'New York, NY'},
                'test/degree': {'value': 'BS'},
                'test/major': {'value': 'Computer Science'},
                'test/gpa': {'value': 4.0}}
        school = Education(uuid4(), 'test', tags)
        self.assertTrue(school.valid)

        # start-date without end-date is valid
        tags = {'test/school-name': {'value': 'New York University'},
                'test/school-location': {'value': 'New York, NY'},
                'test/degree': {'value': 'BS'},
                'test/major': {'value': 'Computer Science'},
                'test/start-date': {'value': '2009-01-01'},
                'test/gpa': {'value': 4.0}}
        school = Education(uuid4(), 'test', tags)
        self.assertTrue(school.valid)
        
        # end-date without start-date is not valid
        tags = {'test/school-name': {'value': 'New York University'},
                'test/school-location': {'value': 'New York, NY'},
                'test/degree': {'value': 'BS'},
                'test/major': {'value': 'Computer Science'},
                'test/end-date': {'value': '2009-01-01'},
                'test/gpa': {'value': 4.0}}
        school = Education(uuid4(), 'test', tags)
        self.assertFalse(school.valid)

        # gpa is not required
        tags = {'test/school-name': {'value': 'New York University'},
                'test/school-location': {'value': 'New York, NY'},
                'test/degree': {'value': 'BS'},
                'test/major': {'value': 'Computer Science'},
                'test/start-date': {'value': '2009-01-01'}}
        school = Education(uuid4(), 'test', tags)
        self.assertTrue(school.valid)

        
    def testEducationFromResponse(self):
        tags1 = {'test/school-name': {'value': 'New York University'},
                 'test/major': {'value': 'Computer Science'},
                 'test/degree': {'value': 'BS'}}
        uuid1 = uuid4()
        work1 = Education(uuid1, 'test', tags1)
        tags2 = {'test/school-name': {'value': 'New York University'}}
        uuid2 = uuid4()
        work2 = Education(uuid2, 'test', tags2)
        self.assertEqual([work1],
                         Education.from_response('test',{uuid1: tags1,
                                                         uuid2: tags2}))

        
if __name__ == '__main__':
    unittest.main()
