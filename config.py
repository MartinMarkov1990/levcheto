#!flask/bin/python
from datetime import datetime, timedelta
import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

WTF_CSRF_ENABLED = False # change this to true once I figure out the templating
SECRET_KEY = 'you-will-never-guess'

START_TIME = datetime.strptime('2015-04-28 01:46', '%Y-%m-%d %H:%M')
PERIOD_DURATION = timedelta(minutes = 6)
YEARS_COUNT = 5
PERIODS_IN_YEAR = 4
STARTING_YEAR = 2016
PERIOD_NAME = 'Quarter'
STOCK_INFO_PRICE = 100
SEGMENT_INFO_PRICE = 100
COUNTRY_INFO_PRICE = 100
GOLD_OIL_INFO_PRICE = 100