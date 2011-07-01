from flaskext.wtf import Form, TextField, Required, FormField, Length, \
    TextAreaField, IntegerField, PasswordField, Email, DateField, FieldList
from flaskext.wtf.html5 import EmailField, URLField

class AddressForm(Form):
    street_address  = TextField('Street Address')
    city            = TextField('City')
    state           = TextField('State')
    zip_code        = IntegerField('Zip Code')

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(AddressForm, self).__init__(*args, **kwargs)


class PersonForm(Form):
    given_name  = TextField("First Name", [Required()])
    family_name = TextField("Last Name", [Required()])
    role        = TextField("Current Title")
    email       = EmailField("Email", [Email()])
    phone       = TextField("Phone", [Required()])
    address     = FormField(AddressForm)
    summary     = TextAreaField('Personal Statement', [Required()])
    password    = PasswordField('Enter your Fluidinfo password', [Required()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(PersonForm, self).__init__(*args, **kwargs)

class JobForm(Form):
    company     = TextField("Company Name", [Required()])
    url         = TextField("Company URL", [Required()])
    title       = TextField("Job Title", [Required()])
    start_date  = DateField("Start Date", [Required()])
    end_date    = DateField("End Date")
    functions   = TextAreaField("Job Functions (1 per line)", [Required()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(JobForm, self).__init__(*args, **kwargs)

class SchoolForm(Form):
    school_name     = TextField("School Name", [Required()])
    school_location = TextField("School Location")
    url             = TextField("School URL", [Required()])
    degree          = TextField("Degree", [Required()])
    major           = TextField("Major", [Required()])
    gpa             = TextField("GPA")
    start_date      = DateField("Start Date", [Required()])
    end_date        = DateField("End Date")

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(SchoolForm, self).__init__(*args, **kwargs)


class SkillForm(Form):
    skills = TextField("Skills")

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(SkillForm, self).__init__(*args, **kwargs)


#class PublicationForm(Form):
#    title   = TextField("Title", [Required()])
#    journal = TextField("Journal", [Required()])
#    year    = TextField("Year", [Required()])


class ResumeForm(Form):
    person      = FormField(PersonForm)
    jobs        = FieldList(FormField(JobForm))
    schools     = FieldList(FormField(SchoolForm))
    #publications= FieldList(FormField(PublicationForm))
    skills      = FormField(SkillForm)

