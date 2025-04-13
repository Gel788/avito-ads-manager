import os
import sys

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from avito_ads import create_app
from avito_ads.models import db, Category
from avito_ads.services.avito_service import AvitoService

def init_db():
    app = create_app()
    with app.app_context():
        # Удаляем существующие таблицы
        db.drop_all()
        print("Существующие таблицы удалены")
        
        # Создаем новые таблицы
        db.create_all()
        print("Новые таблицы созданы")
        
        # Инициализируем сервис Авито
        avito_service = AvitoService()
        
        # Получаем категории
        categories = avito_service.get_categories()
        
        # Добавляем категории в базу данных
        for cat in categories:
            category = Category.query.filter_by(avito_id=cat['id']).first()
            if not category:
                category = Category(
                    avito_id=cat['id'],
                    name=cat['name']
                )
                db.session.add(category)
        
        # Сохраняем изменения
        db.session.commit()
        print("Категории добавлены в базу данных")

if __name__ == '__main__':
    init_db() 