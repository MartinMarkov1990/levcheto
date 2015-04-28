#!flask/bin/python
from flask import render_template, flash, redirect, g, session, url_for, request
from app import app, lm, db, models, bcrypt
from .forms import LoginForm, GIPForm
from flask.ext.login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from datetime import datetime, time, timedelta
from config import START_TIME, PERIOD_DURATION, YEARS_COUNT, PERIODS_IN_YEAR, STARTING_YEAR, PERIOD_NAME
from math import ceil
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, IntegerField, BooleanField, validators
from wtforms.validators import DataRequired




def current_period():
    """" This calculates the current period in-game """
    cur_per = {}
    cur_per['time_id'] = ceil((datetime.today() - START_TIME) / PERIOD_DURATION)
    cur_per['year_id'] = ceil(cur_per['time_id'] / PERIODS_IN_YEAR)
    cur_per['period_id'] = cur_per['time_id'] - ((cur_per['year_id'] - 1) * PERIODS_IN_YEAR)
    return cur_per
    
def show_current_period(cp):
    """ Make the current_period object pretty in order to print it to users. """
    return 'Year %s, %s %s' % (cp['year_id'] - 1 + STARTING_YEAR,
                                PERIOD_NAME,
                                cp['period_id'])


def create_buy_form_class(stocks, bonds, currency, gold_oil):
    form_fields = {}
    for stock in stocks:
        field_id = 'buy_st_num_{}'.format(stock.stock_id)
        form_fields[field_id] = IntegerField(label=stock.stock_id, default=0)
        
    for bond in bonds:
        field_id = 'buy_bd_num_{}'.format(bond.bond_details.currency_code)
        form_fields[field_id] = IntegerField(label=bond.bond_details.country_name, default=0)
        
    for cur in currency:
        field_id = 'buy_cu_num_{}'.format(cur.currency_code)
        form_fields[field_id] = IntegerField(label=cur.currency_code, default=0)
        
    for go in gold_oil:
        field_id = 'buy_go_num_{}'.format(go.gold_oil)
        form_fields[field_id] = IntegerField(label=go.gold_oil, default=0)
    
    return type('BuyForm', (Form,), form_fields)
    
def create_sell_form_class(stocks, bonds, currency, gold_oil):
    form_fields = {}
    for stock in stocks:
        field_id = 'sell_st_num_{}'.format(stock.owned_stocks.id)
        form_fields[field_id] = IntegerField(label=stock.owned_stocks.stock_code, default=0)
        
    for bond in bonds:
        field_id = 'sell_bd_num_{}'.format(bond.owned_bonds.id)
        form_fields[field_id] = IntegerField(label=bond.bond_details.country_name, default=0)
        
    for cur in currency:
        field_id = 'sell_cu_num_{}'.format(cur.currency_owned.id)
        form_fields[field_id] = IntegerField(label=cur.currency_owned.currency_code, default=0)
        
    for go in gold_oil:
        field_id = 'sell_go_num_{}'.format(go.gold_oil_owned.id)
        form_fields[field_id] = IntegerField(label=go.gold_oil_owned.gold_oil, default=0)
    
    return type('SellForm', (Form,), form_fields)
    
def create_info_form_class(company_details, segment_information, countries_info, gold_oil_details):
    form_fields = {}
    for company in company_details:
        field_id = 'info_st_num_{}'.format(company.company_details.stock_id)
        form_fields[field_id] = BooleanField(label=company.company_details.stock_id, default=False)
        
    for segment in segment_information:
        field_id = 'info_se_num_{}'.format(segment.id)
        form_fields[field_id] = BooleanField(label=segment.id, default=False)
        
    for country in countries_info:
        field_id = 'info_cu_num_{}'.format(country.currency_code)
        form_fields[field_id] = BooleanField(label=country.currency_code, default=False)
        
    for go in gold_oil_details:
        field_id = 'info_go_num_{}'.format(go.gold_oil)
        form_fields[field_id] = BooleanField(label=go.gold_oil, default=False)
    
    return type('InfoForm', (Form,), form_fields)
    
    
                                
@lm.user_loader
def load_user(id):
    """ This is required by Flask-Login """
    return models.User.query.get(id)

    
@app.before_request
def before_request():
    """ Initialize user and time and save them to the global object """
    g.user = current_user
    g.cp = current_period()
    if g.user.is_authenticated():
        db.session.add(g.user)
        db.session.commit()
        if g.cp['year_id'] <= 0 and request.endpoint != 'before':
            return redirect(url_for('before'))
        g.user.pay_dividents(g.cp)
        if g.cp['year_id'] > YEARS_COUNT and request.endpoint != 'after':
            return redirect(url_for('after'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
    
@app.route('/', methods=["GET", "POST"])
@app.route('/index', methods=["GET", "POST"])
@login_required
def index():
    now = show_current_period(g.cp)
    owned_stocks = g.user.get_owned_stocks(g.cp['time_id'])
    owned_bonds = g.user.get_owned_bonds()
    owned_currency = g.user.get_owned_currency(g.cp['time_id'])
    owned_gold_oil = g.user.get_owned_gold_oil(g.cp['time_id'])
    stocks = g.user.get_stocks(g.cp['time_id'])
    bonds = g.user.get_bonds(g.cp['time_id'])
    currency = g.user.get_currency(g.cp['time_id'])
    gold_oil = g.user.get_gold_oil(g.cp['time_id'])
    BuyForm = create_buy_form_class(stocks, bonds, currency, gold_oil)
    SellForm = create_sell_form_class(owned_stocks, owned_bonds, owned_currency, owned_gold_oil)
    if request.method == 'POST':
        for key in request.form:
            if key.startswith('sell'):
                fm = 'sell'
                break
            if key.startswith('buy'):
                fm = 'buy'
                break
                
        if fm == 'buy':
            buyform = BuyForm(request.form)
            bought_stocks = {}
            bought_bonds = {}
            bought_currency = {}
            bought_gold_oil = {}
            sellform = SellForm()
            if buyform.validate:
                for name, value in buyform.data.items():
                    if name.startswith('buy_st_num_'):
                        bought_stocks[name[11:]] = value
                    if name.startswith('buy_bd_num_'):
                        bought_bonds[name[11:]] = value
                    if name.startswith('buy_cu_num_'):
                        bought_currency[name[11:]] = value
                    if name.startswith('buy_go_num_'):
                        bought_gold_oil[name[11:]] = value
                        
                g.user.buy_assets(bought_stocks, bought_bonds, bought_currency, bought_gold_oil, g.cp['time_id'])
                
        if fm == 'sell':
            sellform = SellForm(request.form)
            sold_stocks = {}
            sold_bonds = {}
            sold_currency = {}
            sold_gold_oil = {}
            buyform = BuyForm()
            if sellform.validate():
                for name, value in sellform.data.items():
                    if name.startswith('sell_st_num_'):
                        sold_stocks[name[12:]] = value
                    if name.startswith('sell_bd_num_'):
                        sold_bonds[name[12:]] = value
                    if name.startswith('sell_cu_num_'):
                        sold_currency[name[12:]] = value
                    if name.startswith('sell_go_num_'):
                        sold_gold_oil[name[12:]] = value
                        
                g.user.sell_assets(sold_stocks, sold_bonds, sold_currency, sold_gold_oil, g.cp['time_id'])
                
        return redirect(url_for('index'))
            
    else:    
        buyform = BuyForm()
        sellform = SellForm()
    return render_template('index.html',
                           title='Home',
                           user = g.user,
                           now = now,
                           owned_stocks = owned_stocks,
                           owned_bonds = owned_bonds,
                           owned_currency = owned_currency,
                           owned_gold_oil = owned_gold_oil,
                           stocks = stocks,
                           bonds = bonds,
                           currency = currency,
                           gold_oil = gold_oil,
                           buyform = buyform,
                           sellform = sellform)

@app.route("/login", methods=["GET", "POST"])
def login():
    """For GET requests, display the login form. For POSTS, login the current user
    by processing the form."""
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = models.User.query.get(form.email.data)
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                user.authenticated = True
                db.session.add(user)
                db.session.commit()
                login_user(user, remember=True)
                flash('Successful login.')
                return redirect(request.args.get('next') or url_for('index'))
            else:
                flash('Invalid login. Please try again.')
        else:
            flash('User not found. Please try again.')
    return render_template("login.html", form=form)

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """Logout the current user."""
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return redirect(url_for('index'))
    
@app.route("/before")
@login_required
def before():
    return render_template('before.html')
    
@app.route("/after")
@login_required
def after():
    return render_template('after.html', total = g.user.assets_value(YEARS_COUNT * PERIODS_IN_YEAR))
    
    
@app.route("/info", methods=["GET", "POST"])
@login_required
def info():
    now = show_current_period(g.cp)
    company_details = g.user.get_company_details()
    segment_information = g.user.get_segment_information()
    countries_info = g.user.get_countries_info()
    gold_oil_details = g.user.get_gold_oil_details()
    owned_company_details = g.user.get_owned_company_details(g.cp)
    owned_segment_information = g.user.get_owned_segment_information(g.cp)
    owned_countries_info = g.user.get_owned_countries_info(g.cp)
    owned_gold_oil_details = g.user.get_owned_gold_oil_details(g.cp)
    InfoForm = create_info_form_class(company_details, segment_information, countries_info, gold_oil_details)
    years_array = range(1, 1 + g.cp['year_id'])
    if request.method == 'POST':
        infoform = InfoForm(request.form)
        info_companies = {}
        info_segments = {}
        info_countries = {}
        info_gold_oil = {}
        if infoform.validate():
            for name, value in infoform.data.items():
                if name.startswith('info_st_num_'):
                    info_companies[name[12:]] = value
                if name.startswith('info_se_num_'):
                    info_segments[name[12:]] = value
                if name.startswith('info_cu_num_'):
                    info_countries[name[12:]] = value
                if name.startswith('info_go_num_'):
                    info_gold_oil[name[12:]] = value
                    
            g.user.buy_info(info_companies, info_segments, info_countries, info_gold_oil, g.cp)
            
    else:
        infoform = InfoForm()
        
    return render_template('info.html',
                           title='Home',
                           user = g.user,
                           now = now,
                           company_details = company_details,
                           segment_information = segment_information,
                           countries_info = countries_info,
                           gold_oil_details = gold_oil_details,
                           owned_company_details = owned_company_details,
                           owned_segment_information = owned_segment_information,
                           owned_countries_info = owned_countries_info,
                           owned_gold_oil_details = owned_gold_oil_details,
                           infoform = infoform,
                           years_array = years_array,
                           starting_year = STARTING_YEAR)
    
@app.route("/GIP", methods=["GET", "POST"])
@app.route("/gip", methods=["GET", "POST"])
@login_required
def gip():
    now = show_current_period(g.cp)
    if request.method == 'POST':
        form = GIPForm(request.form)
        flash('{} - {}'.format(form.country.data, form.segment.data))
        if form.validate():
            g.user.go_GIP(form.country.data, form.segment.data, g.cp)
    else:
        form = GIPForm()
    return render_template("gip.html", user = g.user, now = now, form=form)