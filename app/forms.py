#!flask/bin/python
import os
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, validators, SelectField
from wtforms.validators import DataRequired
from flask.ext.login import LoginManager
from config import basedir

class LoginForm(Form):
    email = StringField('Email Address', [validators.Length(min=5, max=120)])
    password = PasswordField('Password', [validators.Required()])
    
    
class GIPForm(Form):
    country = SelectField('Country', choices = [("Германия - ЕС", "Германия - ЕС"), ("САЩ", "САЩ"), ("Русия", "Русия"), ("Китай", "Китай"), ("Бразилия", "Бразилия")])
    segment = SelectField('Segment', choices = [("IT", "IT"), ("Tourism", "Tourism"), ("Retail", "Retail"), ("Insurance", "Insurance"), ("Pharma", "Pharma")])