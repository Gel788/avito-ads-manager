from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from avito_ads.config.config import Config
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация расширений
db = SQLAlchemy()
csrf = CSRFProtect()

def create_app(config_class=Config):
    """Создание и настройка приложения"""
    try:
        # Создаем приложение
        app = Flask(__name__)
        
        # Загружаем конфигурацию
        app.config.from_object(config_class)
        
        # Инициализируем расширения
        db.init_app(app)
        csrf.init_app(app)
        
        # Регистрируем blueprint
        from avito_ads.routes import main_bp
        app.register_blueprint(main_bp)
        
        # Создаем необходимые директории
        import os
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        logger.info("Приложение успешно инициализировано")
        return app
        
    except Exception as e:
        logger.error(f"Ошибка при создании приложения: {str(e)}")
        raise
