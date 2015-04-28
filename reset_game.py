#!flask/bin/python
from app import db, models


for i in models.owned_stocks.query.all():
    db.session.delete(i)
    
for i in models.owned_bonds.query.all():
    db.session.delete(i)
    
for i in models.currency_owned.query.all():
    db.session.delete(i)
    
for i in models.gold_oil_owned.query.all():
    db.session.delete(i)
    
for i in models.stock_info_owned.query.all():
    db.session.delete(i)
    
for i in models.country_info_owned.query.all():
    db.session.delete(i)

for i in models.segments_info_owned.query.all():
    db.session.delete(i)
    
for i in models.gold_oil_info_owned.query.all():
    db.session.delete(i)    
    
for i in models.GIP_EPs.query.all():
    db.session.delete(i)
    
for i in models.User.query.all():
    i.lv = 10000
    i.blocked = False
    
db.session.commit()
    
