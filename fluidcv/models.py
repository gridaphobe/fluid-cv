import gae_fluidinfo as fluid
import logging
import os
try:
    import json
except ImportError:
    from django.utils import simplejson as json
from helpers import fluid_filter

def create_object(about):
    fluid.login('fluidcv', app.config['FLUIDCV_PASSWORD'])
    resp = fluid.post('/objects', about)
    fluid.logout()
    return resp

class FluidObject(object):
    """Base class for Fluidinfo objects"""
    TAGS = {}

    def __init__(self, uid, user, tags):
        self.uid = uid
        self.user = user
        for key, val in tags.iteritems():
            # strip off namespaces from tags
            key = os.path.basename(key).replace('-', '_')
            setattr(self, key, val['value'])
        # initialize any tags that haven't been set in fluidinfo
        # this will probably go away soon...    
        for tag in type(self).TAGS:
            if not hasattr(self, tag.replace('-','_')):
                setattr(self, tag.replace('-','_'), '')


    def __eq__(self, other):
        # this is really only overridden to help with testing
        return self.__dict__ == other.__dict__

    @classmethod
    def filter(cls, query, user, async=False):
        query = query % user
        tags = ['%s/%s' % (user, tag) for tag in cls.TAGS.keys()]
        tags.append('fluiddb/about')
        rpc = fluid.get('/values', query=query, tags=tags, async=async)
        return rpc


    @classmethod
    def from_response(cls, user, response):
        objects = []
        for (uuid, tags) in response.items():
            obj = cls(uuid, user, tags)
            if obj.valid:
                objects.append(obj)
        return objects
    

    def reload_tags(self):
        tags = ['%s/%s' % (self.user, tag) for tag in self.TAGS.keys()]
        # quick fix to not retrieve person's pic yet
        try:
            tags.remove('%s/picture' % self.user)
        except ValueError:
            pass
        values = self._get_values(tags)
        try:
            values = values['results']['id'].values()[0]
        except:
            # no values returned
            return
        for key, val in values.iteritems():
            # strip off namespaces from tags
            key = os.path.basename(key).replace('-', '_')
            setattr(self, key, val['value'])

    def _get_tag_value(self, tagpath):
        resp = fluid.get('/objects/%s/%s' % (self.uid, tagpath))
        if resp:
            return resp.content
        return ''

    def _get_values(self, tags):
        query = 'fluiddb/about="%s"' % self.about
        resp = fluid.get('/values', query=query, tags=tags)
        if resp:
            return resp.content
        return {}

    def _set_values(self, tags, user, password):
        fluid.login(user, password)
        try:
            body={}
            for tag, val in tags.iteritems():
                body['%s/%s' % (user, tag)] = {'value' : val}
            query = 'fluiddb/about="%s"' % self.about
            resp = fluid.put('/values', body={
                'queries': [
                    [ query, body ]
                    ]
                }, async=True)
            return resp
        finally:
            fluid.logout()
        #app.fluid.login(user, password)
        #body = {}
        #for tag, val in tags.iteritems():
        #    body['%s/%s' % (user, tag)] = {'value' : val}
        #try:
        #    resp = app.fluid.values.put('fluiddb/about="%s"' % self.about, body)
        #    logging.info('put /values for about="%s" returned %s status' % (
        #                  self.about, resp.status))
        #    return True
        #except Fluid404Error:
        #    # need to create tags first
        #    for tag in tags:
        #        namespace, tag = os.path.split(tag)
        #        # find the proper tag path for our new tag
        #        # if namespace is '', there will be a trailing '/'...
        #        tagpath = os.path.join(user, namespace).rstrip('/')
        #        logging.info('post %s body=%s' % (tagpath, body))
        #        try:
        #            resp = app.fluid.tags[tagpath].post(tag, '', False)
        #        except Fluid412Error, e:
        #            resp = e
        #        logging.info('post to %s returned %s status' % (tagpath,
        #                                                        resp.status))
        #    # now try again..
        #    resp = app.fluid.values.put('fluiddb/about="%s"' % self.about, body)
        #    logging.info('put /values for about="%s" returned %s status' % (
        #        self.about, resp.status))
        #    return True
        #except Fluid401Error:
        #    # permission denied
        #    return False
        #finally:
        #    app.fluid.logout()


class Person(FluidObject):
    TAGS = {'given-name'    : 'your first name',
            'family-name'   : 'your last name',
            'email'         : 'your email address',
            'cell-phone'    : 'your phone number',
            'street-address': 'your street address',
            'locality'      : 'the city you live in',
            'region'        : 'the state/region you live in',
            'postal-code'   : 'your postal code',
            'role'          : 'your current title (i.e. student, developer)',
            'summary'       : 'your statement of purpose',
            'picture'       : 'a picture of you (optional)'}

    def __init__(self, uid, user, tags):
        # remove picture tag
        try:
            del(tags['%s/picture' % user])
        except KeyError:
            pass
        super(Person, self).__init__(uid, user, tags)
        # if given-name and family-name don't exist we will
        # be clever and use fluiddb/users/name instead
        if not (self.given_name or self.family_name):
            name = fluid.get('/about/%s/fluiddb/users/name' % self.about)
            name = name.content.split()
            # in case the user did not specify a full name we will
            # treat the specified name as their first name
            self.given_name = name.pop(0)
            self.family_name = ' '.join(name)
            

    def update_from_form(self, form):
        """Updates the Person Object from the given form"""
        tags = {}
        tags['given-name']     = form.given_name.data
        tags['family-name']    = form.family_name.data
        tags['email']          = form.email.data
        tags['cell-phone']     = form.phone.data
        tags['street-address'] = form.address.street_address.data
        tags['locality']       = form.address.city.data
        tags['region']         = form.address.state.data
        tags['postal-code']    = form.address.zip_code.data
        tags['summary']        = form.summary.data
        tags['role']           = form.role.data
        password               = form.password.data

        return self._set_values(tags, self.user, password)

    @property
    def picture(self):
        """The Person's picture"""
        return 'http://fluiddb.fluidinfo.com/objects/%s/%s/picture' % (
                self.uid, self.user)


class Publication(FluidObject):
    TAGS = {'publication/title'     : 'The title of the publication',
            'publication/journal'   : 'The journal it was published in',
            'publication/year'      : 'The year it was published'}


class Education(FluidObject):
    TAGS = {'attended'          : 'Empty tag signifying that you attended this school',
            'school-name'       : 'The name of the school',
            'school-location'   : 'The location of the school',
            'major'             : 'Your major',
            'degree'            : 'Your degree',
            'start-date'        : 'The date you started',
            'end-date'          : 'The date you graduated',
            'gpa'               : 'Your GPA (optional)'}

    @classmethod
    def create(cls, about, user):
        """Creates a new Education Object in Fluidinfo"""
        resp = create_object(about)
        logging.info("POST to /objects returned %s status" % resp.status)
        return Education(resp.content['id'], user)

    @property
    def valid(self):
        """Determines whether an Education object is in a valid state."""
        return self.school_name and self.major and self.degree and not (
            self.end_date and not self.start_date)

    def update_from_form(self, form, password):
        """Updates an Education Object from the given form"""

        tags = {}
        tags['school-name'] = form.school_name.data
        tags['school-location'] = form.school_location.data
        tags['start-date'] = form.start_date.data.isoformat()
        tags['end-date'] = form.end_date.data
        tags['gpa'] = form.gpa.data
        tags['degree'] = form.degree.data
        tags['major'] = form.major.data
        tags['attended'] = None

        return self._set_values(tags, self.user, password)


class Work(FluidObject):
    TAGS = {'employer'  : 'Empty tag signifying that you worked for this company',
            'company'   : 'The name of the company',
            'title'     : 'Your job title',
            'start-date': 'The date you started',
            'end-date'  : 'The date you left',
            'functions' : 'Your job description'}

    @property
    def valid(self):
        """Determines if the Work object is in a valid state."""
        # the invalid states are when we have no title, or an
        # end-date with no start-date
        if not self.title or (self.end_date and not self.start_date):
            return False
        else:
            return True
        
    @classmethod
    def create(cls, about, user):
        """Creates a new Work Object in Fluidinfo"""
        resp = create_object(about)
        logging.info('POST to /objects returned %s status' % resp.status)
        return Work(resp.content['id'], user)

    def update_from_form(self, form, password):
        """Updates a Work Object from the given form"""

        tags = {}
        tags['company'] = form.company.data
        tags['title'] = form.title.data
        tags['start-date'] = form.start_date.data.isoformat()
        tags['end-date'] = form.end_date.data#.isoformat()
        tags['functions'] = [f.strip() for f in form.functions.data.split("\n")]
        tags['employer'] = None

        return self._set_values(tags, self.user, password)


class OReillySkill(FluidObject):
    """Represents a skill related to a specific O'Reilly book.
    """
    TAGS = {'title'       : '',
            'cover-small' : '',
            'homepage'    : ''}

    def __init__(self, uid, tags):
        super(OReillySkill, self).__init__(uid, 'oreilly.com', tags)

    # FIXME: this is a copy/paste from FluidObject because
    # of clashing function arity in __init__    
    @classmethod
    def from_response(cls, response):
        objects = []
        for (uuid, tags) in response.items():
            obj = cls(uuid, tags)
            if obj.valid:
                objects.append(obj)
        return objects

    @property
    def valid(self):
        return self.title and self.cover_small and self.homepage

    
    @classmethod
    def update_from_form(cls, form, user, password):
        uids = form.skills.data.split(',')
        fluid.login(user, password)
        fluid.post('/tags/%s' % user, {'name': 'skill',
                                       'description': 'My skills',
                                       'indexed': False})
        fluid.delete('/values', query="has %s/skill" % user,
                                tags=["%s/skill" % user])
        for uid in uids:
            resp = fluid.put('/objects/%s/%s/skill' % (uid, user), None)
            if not resp or (resp and resp.status_code != 204):
                logging.warning("PUT /objects/%s/%s/skill failed!" % (uid,user))
        fluid.logout()
