import os
import logging
from flask_sqlalchemy import SQLAlchemy

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация БД
db = SQLAlchemy()

def init_db(app):
    """Инициализация базы данных"""
    try:
        # Инициализация Flask-SQLAlchemy
        db.init_app(app)
        logger.info("База данных успешно инициализирована")
        return True
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {str(e)}")
        return False 