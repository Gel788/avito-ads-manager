import os
import sys
from flask import Flask
from avito_ads.config.config import Config
from avito_ads.models.ad_model import db, Category

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def create_test_categories():
    """Создает тестовые категории в базе данных"""
    with app.app_context():
        # Создаем таблицы, если они не существуют
        db.create_all()
        
        # Проверяем, есть ли уже категории
        if Category.query.count() == 0:
            # Создаем основные категории
            categories = [
                Category(name='Транспорт', avito_id='1'),
                Category(name='Недвижимость', avito_id='2'),
                Category(name='Электроника', avito_id='3'),
                Category(name='Работа', avito_id='4'),
                Category(name='Услуги', avito_id='5')
            ]
            
            # Добавляем категории в базу данных
            for category in categories:
                db.session.add(category)
            
            # Сохраняем изменения
            db.session.commit()
            print("Тестовые категории успешно созданы")
        else:
            print("Категории уже существуют в базе данных")

if __name__ == '__main__':
    app = create_app()
    create_test_categories() 