from avito_ads.database import db

# Таблица связи объявлений и категорий (many-to-many)
ad_categories = db.Table('ad_categories',
    db.Column('ad_id', db.Integer, db.ForeignKey('ads.id', ondelete='CASCADE'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True),
    extend_existing=True
) 