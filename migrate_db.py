import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base
from avito_ads.config.config import Config
from avito_ads.database import db
from avito_ads.models.ad_model import Ad, Category, ad_category
from avito_ads.app import app
import sqlalchemy as sa
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from flask import Flask
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Получаем строку подключения из переменной окружения
DATABASE_URL = os.getenv('DATABASE_URL')

Base = declarative_base()

def execute_query(conn, query, params=None):
    """Выполняет SQL-запрос и возвращает результат"""
    with conn.cursor() as cursor:
        cursor.execute(query, params or ())
        try:
            return cursor.fetchall()
        except psycopg2.ProgrammingError:
            return None

def column_exists(conn, table, column):
    """Проверяет существование колонки в таблице"""
    query = """
    SELECT column_name FROM information_schema.columns 
    WHERE table_name = %s AND column_name = %s;
    """
    result = execute_query(conn, query, (table, column))
    return bool(result)

def add_column(conn, table, column, data_type):
    """Добавляет колонку в таблицу, если она не существует"""
    if not column_exists(conn, table, column):
        query = f"ALTER TABLE {table} ADD COLUMN {column} {data_type};"
        execute_query(conn, query)
        print(f"Колонка '{column}' успешно добавлена в таблицу '{table}'")
    else:
        print(f"Колонка '{column}' уже существует в таблице '{table}'")

def migrate_database():
    """Миграция базы данных"""
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    inspector = inspect(engine)
    
    # Создаем все таблицы
    Ad.metadata.create_all(engine)
    Category.metadata.create_all(engine)
    
    # Создаем сессию
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Проверяем наличие категорий
        categories = session.query(Category).all()
        if not categories:
            # Добавляем базовые категории
            default_categories = [
                Category(name='Мебель и интерьер', avito_id='1'),
                Category(name='Деревообработка', avito_id='2'),
                Category(name='Строительные материалы', avito_id='3'),
                Category(name='Столы и стулья', avito_id='4'),
                Category(name='Шкафы и комоды', avito_id='5'),
                Category(name='Кровати и матрасы', avito_id='6'),
                Category(name='Двери и окна', avito_id='7'),
                Category(name='Пиломатериалы', avito_id='8'),
                Category(name='Фурнитура', avito_id='9'),
                Category(name='Инструменты', avito_id='10'),
                Category(name='Отделочные материалы', avito_id='11'),
                Category(name='Садовая мебель', avito_id='12')
            ]
            session.add_all(default_categories)
            session.commit()
            print("Добавлены базовые категории")
    except Exception as e:
        print(f"Ошибка при инициализации категорий: {str(e)}")
        session.rollback()
    
    # Проверяем и обновляем поля
    with engine.connect() as conn:
        try:
            # Обновляем значения по умолчанию
            conn.execute(text('''
                UPDATE ads 
                SET photo_paths = '[]'::jsonb 
                WHERE photo_paths IS NULL
            '''))
            conn.execute(text('''
                UPDATE ads 
                SET publication_hours = '[]'::jsonb 
                WHERE publication_hours IS NULL
            '''))
            conn.execute(text('''
                UPDATE ads 
                SET ad_metadata = '{}'::jsonb 
                WHERE ad_metadata IS NULL
            '''))
            conn.execute(text('''
                UPDATE ads 
                SET updated_at = created_at 
                WHERE updated_at IS NULL
            '''))
            
            # Обрабатываем дублирование категорий
            conn.execute(text('''
                WITH duplicates AS (
                    SELECT id, avito_id,
                           ROW_NUMBER() OVER (PARTITION BY avito_id ORDER BY id) as rn
                    FROM categories
                )
                DELETE FROM categories 
                WHERE id IN (
                    SELECT id 
                    FROM duplicates 
                    WHERE rn > 1
                )
            '''))
            print("Удалены дублирующиеся категории")
            
            conn.commit()
            print("Миграция базы данных завершена успешно")
            
        except Exception as e:
            print(f"Ошибка при миграции: {str(e)}")
            conn.rollback()
            raise

def init_db():
    """Инициализация базы данных"""
    try:
        # Создаем приложение
        app = Flask(__name__)
        app.config.from_object(Config)
        
        # Инициализируем базу данных
        db.init_app(app)
        
        with app.app_context():
            # Создаем все таблицы
            db.create_all()
            
            # Проверяем наличие категорий
            if Category.query.count() == 0:
                logger.info("Создаем тестовые категории...")
                
                # Создаем корневые категории
                categories = [
                    Category(name="Недвижимость", avito_id="1"),
                    Category(name="Транспорт", avito_id="2"),
                    Category(name="Работа", avito_id="3"),
                    Category(name="Услуги", avito_id="4"),
                    Category(name="Личные вещи", avito_id="5"),
                    Category(name="Для дома и дачи", avito_id="6"),
                    Category(name="Бытовая электроника", avito_id="7"),
                    Category(name="Хобби и отдых", avito_id="8"),
                    Category(name="Животные", avito_id="9"),
                    Category(name="Для бизнеса", avito_id="10")
                ]
                
                # Добавляем категории в базу данных
                for category in categories:
                    db.session.add(category)
                
                db.session.commit()
                logger.info("Тестовые категории успешно созданы")
            else:
                logger.info("Категории уже существуют в базе данных")
            
            logger.info("База данных успешно инициализирована")
            
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {str(e)}")
        raise

if __name__ == '__main__':
    init_db() 