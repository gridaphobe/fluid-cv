# This Python file uses the following encoding: utf-8
#import httplib2
import gae_fluidinfo as fluid
import logging
import os
import re
try:
    import json
except ImportError:
    from django.utils import simplejson as json
from datetime import datetime
from flask import Flask, abort, request, render_template, flash, redirect, g
from google.appengine.api import urlfetch
from pprint import pformat

from forms import ResumeForm
from helpers import fluid_filter, states, url_re
from models import Person, Education, Work, Publication, OReillySkill

app = Flask(__name__)
app.config.from_object('fluidcv.settings')

@app.route('/')
def index():
    person_doc = Person.TAGS
    work_doc   = Work.TAGS
    school_doc = Education.TAGS
    return render_template('index.html', person_doc=person_doc,
            work_doc=work_doc, school_doc=school_doc)


@app.route('/<user>')
def cv(user):
    person_rpc = Person.async_filter('fluiddb/users/username="%s"', user)
    # check for person's picture
    #logging.debug('Checking for %s/picture at %s' % (user, person.picture))
    #h = httplib2.Http()
    #head, cont = h.request(person.picture, 'HEAD')
    #if head['status'] == '200':
    #    person.has_pic = True
    #    logging.debug('%s/picture exists' % user)
    #else:
    #    person.has_pic = False
    #    logging.debug('%s/picture does not exist. Returned %s status' % (
    #        user, head['status']))
    # find user's jobs
    work_rpc = Work.async_filter('has %s/employer', user)
    # find user's schools
    school_rpc = Education.async_filter('has %s/attended', user)
    # find user's publications
    #publications = fluid_filter('has %s/publication' % user)
    #publications = [Publication(uid, user) for uid in publications]
    publications = []
    # find user's skills associated with o'reilly books
    oskill_rpc = OReillySkill.async_filter(
            'has %s/skill and has %%s/title' % user, 'oreilly.com')
    resp = fluid.result(person_rpc)
    if resp.status_code == 204:
        print resp.status_code
        uid, tags = resp.content['results']['id'].items()[0]
        person = Person(uid, user, tags)
    else:
        logging.info('Person filter for %s returned %d' % (user, resp.status_code))
        abort(404)
    resp = fluid.result(work_rpc)
    if resp.status_code == 204:
        jobs = resp.content['results']['id']
        jobs = [Work(uid, user, tags) for (uid, tags) in jobs.items()]
    else:
        #FIXME need better error handling
        logging.info('Work filter for %s returned %d' % (user, resp.status_code))
        abort(404)
    resp = fluid.result(school_rpc)
    if resp.status_code == 204:
        schools = resp.content['results']['id']
        schools = [Education(uid, user, tags) for (uid, tags) in schools.items()]
    else:
        logging.info('School filter for %s returned %d' % (user, resp.status_code))
        abort(404)
    resp = fluid.result(oskill_rpc)
    if resp.status_code == 204:
        oskills = resp.content['results']['id']
        oskills = [OReillySkill(uid, tags) for (uid, tags) in oskills.items()]
    else:
        logging.info('Skill filter for %s returned %d' % (user, resp.status_code))
        abort(404)

    return render_template('cv.html', person=person, jobs=jobs,
                           schools=schools, publications=publications,
                           oskills=oskills,
                           current_date=datetime.now().date())

@app.route('/<user>/edit', methods=['GET', 'POST'])
def edit(user):
    person = fluid_filter('fluiddb/users/username="%s"' % user)
    if not person:
        abort(404)
    form = ResumeForm()
    person = Person(person[0], user)
    jobs = fluid_filter('has %s/employer' % user)
    jobs = [Work(uid, user) for uid in jobs]
    for job in jobs:
        form.jobs.append_entry()
        # join functions list to paragraph
        job.functions = r"\n".join(job.functions).strip()

    schools = fluid_filter('has %s/attended' % user)
    schools = [Education(uid, user) for uid in schools]
    for school in schools:
        form.schools.append_entry()

    if form.validate_on_submit():
        denied = False
        logging.debug('Valid form for %s' % user)
        password = form.person.password.data

        if not person.update_from_form(form.person):
            denied = True

        for job_form in form.jobs:
            # it seems that we get 1 or more phantom jobs here...
            if not job_form.url.data:
                continue
            # this seems kinda weird, but I'm not sure of a better way to
            # find the correct work object yet
            found_job = False
            logging.info("working on job: %s" % job_form.url.data)
            for job in jobs:
                if job.about == job_form.url.data:
                    if not job.update_from_form(job_form, password):
                        denied = True
                    found_job = True

            if not found_job:
                job = Work.create(job_form.url.data, user)
                if not job.update_from_form(job_form, password):
                    denied = True

        for school_form in form.schools:
            # it seems that we get 1 or more phantom schools here...
            if not school_form.url.data:
                continue
            # this seems kinda weird, but I'm not sure of a better way to
            # find the correct work object yet
            found_school = False
            logging.info("working on school: %s" % school_form.url.data)
            for school in schools:
                if school.about == school_form.url.data:
                    if not school.update_from_form(school_form, password):
                        denied = True
                    found_school = True

            if not found_school:
                school = Education.create(school_form.url.data, user)
                if not school.update_from_form(school_form, password):
                    denied = True

        if form.skills.data:
            OReillySkill.update_from_form(form.skills, user, password)

        if denied:
            flash("Permission Denied!", category='error')
        else:
            flash("Success!", category='info')

        # gotta reload the attributes to show changes
        person.reload_tags()
        for job in jobs:
            job.reload_tags()
        for school in schools:
            school.reload_tags()

    skills = fluid_filter('has %s/skill' % user)
    skills = [OReillySkill(uid) for uid in skills]
    skill_list = json.dumps([{'id'   : skill.uid,
                              'name' : skill.title}
                             for skill in skills])

    return render_template('edit.html', person=person, jobs=jobs,
                           schools=schools, form=form, user=user,
                           skill_list=skill_list)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

@app.template_filter('parsedatetimeformat')
def parsedatetimeformat(value, parse_format="%Y-%m-%d", out_format="%b %Y"):
    if value.lower() in ['current', 'present']:
        return value
    return datetime.strptime(value, parse_format).strftime(out_format)

@app.template_filter('expandstate')
def expandstate(state_abbr):
    """Expand the state abbreviation to the full state name"""
    try:
        return states[state_abbr]
    except KeyError:
        # maybe you don't live in the US
        return state_abbr

@app.template_filter('urllinker')
def urllinker(text):
    """Find all URLs and enclose them in <a href='url'>url</a>.
    Do NOT pass in text that already contains proper html links!
    Also, make sure to mark the output as 'safe,' i.e.

        {{ mytext|urllinker|safe }}

    If the output is not marked as 'safe,' Jinja will auto-escape your
    nice new html tag...
    """
    return re.sub(url_re, r'<a href="\1">\1</a>', text)
