#!flask/bin/python
#encoding=UTF-8
from flask import render_template, flash, redirect, g, session, url_for, request
from hashlib import md5
import re
from app import db
from app import app
from math import ceil
from config import START_TIME, PERIOD_DURATION, YEARS_COUNT, PERIODS_IN_YEAR, STARTING_YEAR, PERIOD_NAME,\
    STOCK_INFO_PRICE, SEGMENT_INFO_PRICE, COUNTRY_INFO_PRICE, GOLD_OIL_INFO_PRICE

import sys

class User(db.Model):
    __tablename__ = 'user'

    email = db.Column(db.String, primary_key=True)
    password = db.Column(db.String)
    authenticated = db.Column(db.Boolean, default=False)
    blocked = db.Column(db.Boolean, default=False)
    admin = db.Column(db.Boolean, default=False)
    lv = db.Column(db.Integer, default = 10000)
    owned_stocks = db.relationship('owned_stocks',
                                    backref = 'owner',
                                    lazy='dynamic')
    owned_bonds = db.relationship('owned_bonds',
                                  backref = 'owner',
                                  lazy='dynamic')
    gold_oil_owned = db.relationship('gold_oil_owned',
                                     backref = 'owner',
                                     lazy='dynamic')
    GIP_EP = db.relationship('GIP_EPs',
                             backref = 'EP',
                             lazy = 'dynamic')
                             
    def get_owned_stocks(self, time):
        return db.session.query(User, owned_stocks, stock_price).\
            filter(User.email == self.email).\
            filter(owned_stocks.stock_code == stock_price.stock_id).\
            filter(stock_price.time == time)
            
    def get_owned_bonds(self):
        return db.session.query(User, owned_bonds, bond_details).\
            filter(User.email == self.email).\
            filter(owned_bonds.currency_code == bond_details.currency_code)
            
    def get_owned_currency(self, time):
        return db.session.query(User, currency_owned, currency_price).\
            filter(User.email == self.email).\
            filter(currency_owned.currency_code == currency_price.currency_code).\
            filter(currency_price.time == time)
    
    def get_owned_gold_oil(self, time):
        return db.session.query(User, gold_oil_owned, gold_oil_prices).\
            filter(User.email == self.email).\
            filter(gold_oil_owned.gold_oil == gold_oil_prices.gold_oil).\
            filter(gold_oil_prices.time == time)
            
    
    def get_stocks(self, time):
        return db.session.query(stock_price).filter(stock_price.time == time)
    
    def get_gold_oil(self, time):
        return db.session.query(gold_oil_prices).filter(gold_oil_prices.time == time)
    
    def get_currency(self, time):
        return db.session.query(currency_price).filter(currency_price.time == time)
    
    def get_bonds(self, time):
        return db.session.query(bond_details, bond_interest).\
                filter(bond_details.currency_code == bond_interest.country_code).\
                filter(bond_interest.time == time)
                
    def get_company_details(self):
        return db.session.query(company_details, segments).filter(company_details.segment_id == segments.id)
        
    def get_segment_information(self):
        return db.session.query(segments)
        
    def get_countries_info(self):
        return db.session.query(bond_details)
        
    def get_gold_oil_details(self):
        return db.session.query(gold_oil)
    
    def get_owned_company_details(self, cp):
        return db.session.query(stock_info_owned).filter(stock_info_owned.user_id == self.email).\
                filter(stock_info_owned.year_id <= cp['year_id'])
        
    def get_owned_segment_information(self, cp):
        return db.session.query(segments_info_owned).filter(segments_info_owned.user_id == self.email).\
                filter(segments_info_owned.year_id <= cp['year_id'])
        
    def get_owned_countries_info(self, cp):
        return db.session.query(country_info_owned).filter(country_info_owned.user_id == self.email).\
                filter(country_info_owned.year_id <= cp['year_id'])
        
    def get_owned_gold_oil_details(self, cp):
        return db.session.query(gold_oil_info_owned).filter(gold_oil_info_owned.user_id == self.email).\
                filter(gold_oil_info_owned.year_id <= cp['year_id'])
    
    def buy_value(self, stocks, bonds, currency, gold_oil, time):
        s = 0
        for stock_id, q in stocks.items():
            if q == '' or q is None:
                q = 0
                continue
            if q > 0:
                s = s + db.session.query(stock_price).filter(stock_price.time == time).filter(stock_price.stock_id == stock_id).first().price * q
            
        for currency_code, q in currency.items():
            if q == '' or q is None:
                q = 0
                continue
            if q > 0:
                s = s + db.session.query(currency_price).filter(currency_price.time == time).filter(currency_price.currency_code == currency_code).first().lv_price * q
            
        for g_o, q in gold_oil.items():
            if q == '' or q is None:
                q = 0
                continue
            if q > 0:
                s = s + db.session.query(gold_oil_prices).filter(gold_oil_prices.time == time).filter(gold_oil_prices.gold_oil == g_o).first().price * q
            
        for country_code, q in bonds.items():
            if q == '' or q is None:
                q = 0
                continue
            if q > 0:
                qr = db.session.query(bond_details, currency_price).filter(bond_details.currency_code == currency_price.currency_code).\
                    filter(bond_details.currency_code == country_code).filter(currency_price.time == time)
                s = s + qr.first().bond_details.nominal_value * qr.first().currency_price.lv_price * q

        return s

    def buy_assets(self, stocks, bonds, currency, gold_oil, time):
        s = self.buy_value(stocks, bonds, currency, gold_oil, time)
        if s > self.lv:
            flash('Not enough cash!')
            return redirect(url_for('index'))
        for stock_id, q in stocks.items():
            if q == '' or q is None:
                q = 0
            if q > 0:
                db.session.add(owned_stocks(user_id = self.email,
                                            stock_code = stock_id,
                                            quantity = q,
                                            time_bought = time,
                                            price_bought = db.session.query(stock_price).filter(stock_price.time == time).filter(stock_price.stock_id == stock_id).first().price,
                                            divident_due = ceil(time/PERIODS_IN_YEAR)*PERIODS_IN_YEAR+1))
                                            
        for currency_code, q in currency.items():
            if q == '' or q is None:
                q = 0
            if q > 0:
                db.session.add(currency_owned(user_id = self.email,
                                              currency_code = currency_code,
                                              time_bought = time,
                                              quantity = q,
                                              price_bought = db.session.query(currency_price).\
                                                filter(currency_price.time == time).filter(currency_price.currency_code == currency_code).first().lv_price))
                                                
        for g_o, q in gold_oil.items():
            if q == '' or q is None:
                q = 0
            if q > 0:
                db.session.add(gold_oil_owned(user_id = self.email,
                                              gold_oil = g_o,
                                              time_bought = time,
                                              quantity = q,
                                              price_bought = db.session.query(gold_oil_prices).\
                                                filter(gold_oil_prices.time == time).filter(gold_oil_prices.gold_oil == g_o).first().price))
                                                
        for country_code, q in bonds.items():
            if q == '' or q is None:
                q = 0
            if q > 0:
                qr = db.session.query(bond_details, bond_interest).filter(bond_details.currency_code == bond_interest.country_code).\
                    filter(bond_details.currency_code == country_code).filter(bond_interest.time == time)
                db.session.add(owned_bonds(user_id = self.email,
                                           currency_code = country_code,
                                           quantity = q,
                                           nominal_value = qr.first().bond_details.nominal_value,
                                           interest_rate = qr.first().bond_interest.interest_rate,
                                           interest_due = ceil(time/PERIODS_IN_YEAR)*PERIODS_IN_YEAR+1))
                                           
        self.lv = self.lv - s
        db.session.commit()
        flash('Успешна покупка!')
        return redirect(url_for('index'))
        
    
    def sell_value(self, stocks, bonds, currency, gold_oil, time):
        s = 0
        for stock_id, q in stocks.items():
            if q == '' or q is None:
                q = 0
                continue
            qr = db.session.query(owned_stocks, stock_price).filter(owned_stocks.stock_code == stock_price.stock_id).\
                    filter(owned_stocks.id == stock_id).filter(owned_stocks.user_id == self.email).filter(stock_price.time == time).first()
            q = min(q, qr.owned_stocks.quantity)
            s = s + q*qr.stock_price.price
            
        for bond_id, q in bonds.items():
            if q == '' or q is None:
                q = 0
                continue
            qr = db.session.query(owned_bonds, bond_details, currency_price).filter(owned_bonds.currency_code == bond_details.currency_code).\
                    filter(owned_bonds.currency_code == currency_price.currency_code).filter(owned_bonds.id == bond_id).filter(currency_price.time == time).first()
            q = min(q, qr.owned_bonds.quantity)
            s = s + q*qr.owned_bonds.nominal_value*qr.currency_price.lv_price
            
        for cur_id, q in currency.items():
            if q == '' or q is None:
                q = 0
                continue
            qr = db.session.query(currency_owned, currency_price).filter(currency_owned.currency_code == currency_price.currency_code).\
                    filter(currency_price.time == time).filter(currency_owned == cur_id).first()
            q = min(q, qr.currency_owned.quantity)
            s = s + q*qr.currency_price.lv_price
            
        for g_o, q in gold_oil.items():
            if q == '' or q is None:
                q = 0
                continue
            qr = db.session.query(gold_oil_owned, gold_oil_prices).filter(gold_oil_owned.gold_oil == gold_oil_prices.gold_oil).\
                    filter(gold_oil_owned.id == g_o).filter(gold_oil_prices.time == time).first()
            q = min(q, qr.gold_oil_owned.quantity)        
            s = s + q*qr.gold_oil_prices.price
            
        return s
    
    def sell_assets(self, stocks, bonds, currency, gold_oil, time):
        s = self.sell_value(stocks, bonds, currency, gold_oil, time)
        for stock_id, q in stocks.items():
            if q == '' or q is None:
                q = 0
            qr = db.session.query(owned_stocks).filter(owned_stocks.id == stock_id).first()
            if q >= qr.quantity:
                db.session.delete(qr)
            else:
                qr.quantity = qr.quantity - q
                
        for bond_id, q in bonds.items():
            if q == '' or q is None:
                q = 0
            qr = db.session.query(owned_bonds).filter(owned_bonds.id == bond_id).first()
            if q >= qr.quantity:
                db.session.delete(qr)
            else:
                qr.quantity = qr.quantity - q
                
        for cur_id, q in currency.items():
            if q == '' or q is None:
                q = 0
            qr = db.session.query(currency_owned).filter(currency_owned.id == cur_id).first()
            if q >= qr.quantity:
                db.session.delete(qr)
            else:
                qr.quantity = qr.quantity - q
                
        for g_o, q in gold_oil.items():
            if q == '' or q is None:
                q = 0
            qr = db.session.query(gold_oil_owned).filter(gold_oil_owned.id == g_o).first()
            if q >= qr.quantity:
                db.session.delete(qr)
            else:
                qr.quantity = qr.quantity - q
                
        self.lv = self.lv + s
        db.session.commit()
        flash('Успешна продажба!')
        return redirect(url_for('index'))       
        
    def pay_dividents(self, cp):
        d = 0
        i = 0
        stocks = db.session.query(owned_stocks, stock_divident).filter(owned_stocks.stock_code == stock_divident.stock_id).\
                    filter(owned_stocks.user_id == self.email).filter(owned_stocks.divident_due == cp['time_id']).filter(stock_divident.divident_period == cp['year_id']).\
                    filter(cp['period_id'] == 1)
        for stock in stocks:
            if stock.owned_stocks.divident_due <= cp['time_id'] and stock.owned_stocks.divident_due > 0:
                d = d + stock.owned_stocks.quantity * stock.stock_divident.amount
            
        for ows in db.session.query(owned_stocks).filter(owned_stocks.user_id == self.email).filter(owned_stocks.divident_due == time):
            if ows.divident_due <= cp['time_id'] and ows.divident_due > 0:
                if cp['year_id'] > YEARS_COUNT:
                    ows.divident_due = 0
                else:
                    ows.divident_due = ows.divident_due + PERIODS_IN_YEAR
                db.session.add(ows)    
                
        bonds = db.session.query(owned_bonds).filter(owned_bonds.user_id == self.email).filter(owned_bonds.interest_due == cp['time_id'])
        for bond in bonds:
            if bond.interest_due <= cp['time_id'] and bond.interest_due > 0:
                i = i + bond.quantity * bond.nominal_value * bond.interest_rate
                if cp['year_id'] > YEARS_COUNT:
                    bond.interest_due = 0
                else:
                    bond.interest_due = bond.interest_due + PERIODS_IN_YEAR
                db.session.add(bond)
                
        
        self.lv = self.lv + d + i
        db.session.commit()
        if d > 0:
            flash("Dividend paid: {:.2f} lv".format(d))
        if i > 0:
            flash("Interest paid: {:.2f} lv".format(i))
    
    def info_value(self, info_companies, info_segments, info_countries, info_gold_oil, cp):
        v = 0
        for st, bl in info_companies.items():
            if bl:
                ct = db.session.query(stock_info_owned).filter(stock_info_owned.user_id == self.email).filter(stock_info_owned.year_id == cp['year_id']).\
                        filter(stock_info_owned.stock_id == st).count()
                if ct == 0:
                    v = v + STOCK_INFO_PRICE
                    
        for se, bl in info_segments.items():
            if bl:
                ct = db.session.query(segments_info_owned).filter(segments_info_owned.user_id == self.email).filter(segments_info_owned.year_id == cp['year_id']).\
                        filter(segments_info_owned.segment_id == se).count()
                if ct == 0:
                    v = v + SEGMENT_INFO_PRICE
                    
        for cu, bl in info_countries.items():
            if bl:
                ct = db.session.query(country_info_owned).filter(country_info_owned.user_id == self.email).filter(country_info_owned.year_id == cp['year_id']).\
                        filter(country_info_owned.country_code == cu).count()
                if ct == 0:
                    v = v + COUNTRY_INFO_PRICE
                    
        for go, bl in info_gold_oil.items():
            if bl:
                ct = db.session.query(gold_oil_info_owned).filter(gold_oil_info_owned.user_id == self.email).filter(gold_oil_info_owned.year_id == cp['year_id']).\
                    filter(gold_oil_info_owned.gold_oil == go).count()
                if ct == 0:
                    v = v + GOLD_OIL_INFO_PRICE
                    
        return v                    

                
    def buy_info(self, info_companies, info_segments, info_countries, info_gold_oil, cp):
        v = self.info_value(info_companies, info_segments, info_countries, info_gold_oil, cp)
        if v > self.lv:
            flash('Not enough cash!')
            return redirect(url_for('info'))
        for st, bl in info_companies.items():
            if bl:
                ct = db.session.query(stock_info_owned).filter(stock_info_owned.user_id == self.email).filter(stock_info_owned.year_id == cp['year_id']).\
                        filter(stock_info_owned.stock_id == st).count()
                if ct == 0:
                    qr = db.session.query(stock_divident).filter(stock_divident.stock_id == st).filter(stock_divident.divident_period == cp['year_id']).first()
                    db.session.add(stock_info_owned(user_id = self.email,
                                                    stock_info_id = qr.divident_id,
                                                    stock_id = st,
                                                    year_id = cp['year_id'],
                                                    company_information = qr.company_information))
                    
        for se, bl in info_segments.items():
            if bl:
                ct = db.session.query(segments_info_owned).filter(segments_info_owned.user_id == self.email).filter(segments_info_owned.year_id == cp['year_id']).\
                        filter(segments_info_owned.segment_id == se).count()
                if ct == 0:
                    qr = db.session.query(segments_info).filter(segments_info.segment_id == se).filter(segments_info.year_id == cp['year_id']).first()
                    db.session.add(segments_info_owned( user_id = self.email,
                                                        segment_info_id = qr.id,
                                                        segment_id = se,
                                                        year_id = cp['year_id'],
                                                        segment_info = qr.segment_info))
                    
        for cu, bl in info_countries.items():
            if bl:
                ct = db.session.query(country_info_owned).filter(country_info_owned.user_id == self.email).filter(country_info_owned.year_id == cp['year_id']).\
                        filter(country_info_owned.country_code == cu).count()
                if ct == 0:
                    qr = db.session.query(country_info).filter(country_info.country_code == cu).filter(country_info.year_id == cp['year_id']).first()
                    db.session.add(country_info_owned(  user_id = self.email,
                                                        country_info_id = qr.id,
                                                        country_code = cu,
                                                        year_id = cp['year_id'],
                                                        country_information = qr.country_information))
                    
        for go, bl in info_gold_oil.items():
            if bl:
                ct = db.session.query(gold_oil_info_owned).filter(gold_oil_info_owned.user_id == self.email).filter(gold_oil_info_owned.year_id == cp['year_id']).\
                    filter(gold_oil_info_owned.gold_oil == go).count()
                if ct == 0:
                    qr = db.session.query(gold_oil_info).filter(gold_oil_info.gold_oil == go).filter(gold_oil_info.year_id == cp['year_id']).first()
                    db.session.add(gold_oil_info_owned( user_id = self.email,
                                                        gold_oil_info_id = qr.id,
                                                        gold_oil = go,
                                                        year_id = cp['year_id'],
                                                        gold_oil_information = qr.gold_oil_information))
        
        self.lv = self.lv - v
        db.session.add(self)
        db.session.commit()
        flash("Successful information purchase! {}".format(v))
        return redirect(url_for('info'))
    
    def assets_value(self, time):
        s = 0
        s = s + self.lv
        for stock_id in db.session.query(owned_stocks.id):
            qr = db.session.query(owned_stocks, stock_price).filter(owned_stocks.stock_code == stock_price.stock_id).\
                    filter(owned_stocks.id == stock_id).filter(stock_price.time == time).first()
            s = s + qr.owned_stocks.quantity*qr.stock_price.price
            
        for bond_id in db.session.query(owned_bonds.id):
            qr = db.session.query(owned_bonds, bond_details, currency_price).filter(owned_bonds.currency_code == bond_details.currency_code).\
                    filter(owned_bonds.currency_code == currency_price.currency_code).filter(owned_bonds.id == bond_id).filter(currency_price.time == time).first()
            q = min(q, qr.owned_bonds.quantity)
            s = s + qr.owned_bonds.quantity*qr.owned_bonds.nominal_value*qr.currency_price.lv_price
            
        for cur_id in db.session.query(currency_owned.id):
            qr = db.session.query(currency_owned, currency_price).filter(currency_owned.currency_code == currency_price.currency_code).\
                    filter(currency_price.time == time).filter(currency_owned == cur_id).first()
            s = s + qr.currency_owned.quantity*qr.currency_price.lv_price
            
        for g_o in db.session.query(gold_oil_owned.id):
            qr = db.session.query(gold_oil_owned, gold_oil_prices).filter(gold_oil_owned.gold_oil == gold_oil_prices.gold_oil).\
                    filter(gold_oil_owned.id == g_o).filter(gold_oil_prices.time == time).first()
            s = s + qr.gold_oil_owned.quantity*qr.gold_oil_prices.price
            
        return s
    
    def go_GIP(self, country, segment, cp):
        gipep = GIP_EPs(user_id = self.email, country_name = country, segment_id = segment, departure_time = cp['time_id'], return_time = cp['time_id'] + 2)
        db.session.add(gipep)
        self.blocked = True
        cu_qr_ck = db.session.query(bond_details, country_info_owned).filter(bond_details.currency_code == country_info_owned.country_code).\
                    filter(bond_details.country_name == country).filter(country_info_owned.year_id == cp['year_id'])
        if cu_qr_ck.count() == 0:
            cu_qr = db.session.query(bond_details, country_info).filter(bond_details.currency_code == country_info.country_code).\
                        filter(bond_details.country_name == country).filter(country_info.year_id == cp['year_id']).first()
            db.session.add(country_info_owned(  user_id = self.email,
                                                country_info_id = cu_qr.country_info.id,
                                                country_code = cu_qr.bond_details.currency_code,
                                                year_id = cp['year_id'],
                                                country_information = cu_qr.country_info.country_information))
        se_qr_ck = db.session.query(segments_info_owned).filter(segments_info_owned.segment_id == segment).filter(segments_info_owned.year_id == cp['year_id'])
        if se_qr_ck.count() == 0:
            se_qr = db.session.query(segments_info).filter(segments_info.segment_id == segment).filter(segments_info.year_id == cp['year_id']).first()
            db.session.add(segments_info_owned( user_id = self.email,
                                                segment_info_id = se_qr.id,
                                                segment_id = segment,
                                                year_id = cp['year_id'],
                                                segment_info = se_qr.segment_info))
                                                
        db.session.commit()
        flash('Successfully went to an internship in {0} in the {1} segment.'.format(country, segment))
        return redirect(url_for('info'))
    
    
    
    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False
        

class segments(db.Model):
    id = db.Column(db.String(40), primary_key = True)
    bg_name = db.Column(db.String(60))
    
class company_details(db.Model):
    stock_id = db.Column(db.String(6), primary_key = True)
    company_name = db.Column(db.String(40))
    segment_id = db.Column(db.String(40), db.ForeignKey(segments.id))
    market = db.Column(db.String(40))
    activity = db.Column(db.String(200))
        
class stock_price(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    stock_id = db.Column(db.String(6), db.ForeignKey(company_details.stock_id))
    time = db.Column(db.Integer)
    price = db.Column(db.Float)
    
class stock_divident(db.Model):
    divident_id = db.Column(db.Integer, primary_key = True)
    stock_id = db.Column(db.String(6), db.ForeignKey(company_details.stock_id))
    amount = db.Column(db.Float)
    divident_period = db.Column(db.Integer)
    company_information = db.Column(db.String(200))
    
class stock_info_owned(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.String(120), db.ForeignKey(User.email))
    stock_info_id = db.Column(db.Integer, db.ForeignKey(stock_divident.divident_id))
    stock_id = db.Column(db.String(6), db.ForeignKey(company_details.stock_id))
    year_id = db.Column(db.Integer)
    company_information = db.Column(db.String(200))

class segments_info(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    segment_id = db.Column(db.String(40), db.ForeignKey(segments.id))    
    year_id = db.Column(db.Integer)
    segment_info = db.Column(db.String(200))
    
class segments_info_owned(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    segment_info_id = db.Column(db.Integer, db.ForeignKey(segments_info.id))
    user_id = db.Column(db.String(120), db.ForeignKey(User.email))
    segment_id = db.Column(db.String(40), db.ForeignKey(segments.id))
    year_id = db.Column(db.Integer)
    segment_info = db.Column(db.String(200))
    
class bond_details(db.Model):
    currency_code = db.Column(db.String(10), primary_key = True)
    country_name = db.Column(db.String(30))
    nominal_value = db.Column(db.Integer)
    
class bond_interest(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    country_code = db.Column(db.String(30), db.ForeignKey(bond_details.currency_code))
    time = db.Column(db.Integer)
    interest_rate = db.Column(db.Integer)
    
class currency_price(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    currency_code = db.Column(db.String(10), db.ForeignKey(bond_details.currency_code))
    time = db.Column(db.Integer)
    lv_price = db.Column(db.Float)
    
class country_info(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    country_code = db.Column(db.String(30), db.ForeignKey(bond_details.currency_code))
    year_id = db.Column(db.Integer)
    country_information = db.Column(db.String(200))
    
class country_info_owned(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    country_info_id = db.Column(db.Integer, db.ForeignKey(country_info.id))
    user_id = db.Column(db.String(120), db.ForeignKey(User.email))
    country_code = db.Column(db.String(30), db.ForeignKey(bond_details.currency_code))
    year_id = db.Column(db.Integer)
    country_information = db.Column(db.String(200))

class gold_oil(db.Model):
    gold_oil = db.Column(db.String(5), primary_key = True)
    
class gold_oil_prices(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    gold_oil = db.Column(db.String(5), db.ForeignKey(gold_oil.gold_oil)) # change this, don't know how.
    time = db.Column(db.Integer)
    price = db.Column(db.Float)
    
class gold_oil_info(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    gold_oil = db.Column(db.String(5), db.ForeignKey(gold_oil.gold_oil))
    year_id = db.Column(db.Integer)
    gold_oil_information = db.Column(db.String(200))
    
class gold_oil_info_owned(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    gold_oil_info_id = db.Column(db.Integer, db.ForeignKey(gold_oil_info.id))
    user_id = db.Column(db.String(120), db.ForeignKey(User.email))
    gold_oil = db.Column(db.String(30), db.ForeignKey(gold_oil.gold_oil))
    year_id = db.Column(db.Integer)
    gold_oil_information = db.Column(db.String(200))
    
class owned_stocks(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.String(120), db.ForeignKey(User.email))
    stock_code = db.Column(db.Integer, db.ForeignKey(company_details.stock_id))
    quantity = db.Column(db.Integer)
    time_bought = db.Column(db.Integer)
    price_bought = db.Column(db.Float)
    divident_due = db.Column(db.Integer)
    
class owned_bonds(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.String(120), db.ForeignKey(User.email))
    currency_code = db.Column(db.String(10), db.ForeignKey(bond_details.currency_code))
    nominal_value = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    interest_rate = db.Column(db.Float)
    interest_due = db.Column(db.Integer)
    
class currency_owned(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.String(120), db.ForeignKey(User.email))
    currency_code = db.Column(db.String)
    time_bought = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    price_bought = db.Column(db.Float)
    
class gold_oil_owned(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.String(120), db.ForeignKey(User.email))
    gold_oil = db.Column(db.String(5)) # change this, don't know how.
    time_bought = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    price_bought = db.Column(db.Float)

class GIP_EPs(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.String(120), db.ForeignKey(User.email))
    country_name = db.Column(db.String(30))
    segment_id = db.Column(db.String(40), db.ForeignKey(segments.id))
    departure_time = db.Column(db.Integer)
    return_time = db.Column(db.Integer)