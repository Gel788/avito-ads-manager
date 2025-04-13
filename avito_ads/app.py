import os
import logging
import threading
from flask import Flask
from flask_bootstrap import Bootstrap4
from flask_wtf.csrf import CSRFProtect

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app')

# Создаем необходимые директории
for directory in ['instance', 'logs', 'avito_ads/static/uploads']:
    path = os.path.join(os.getcwd(), directory)
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        try:
            os.chmod(path, 0o777)
        except Exception as e:
            print(f"Ошибка при установке прав доступа для {path}: {str(e)}")

# Создаем Flask-приложение
app = Flask(__name__)

# Загружаем конфигурацию
from avito_ads.config.config import Config
app.config.from_object(Config)

# Инициализация расширений
csrf = CSRFProtect(app)
bootstrap = Bootstrap4(app)

# Инициализация базы данных
from avito_ads.database import db
db.init_app(app)

# Импортируем модели до создания таблиц
from avito_ads.models.ad_model import Ad, Category

# Создаем таблицы базы данных
with app.app_context():
    try:
        # Создаем таблицы принудительно
        db.create_all()
        logger.info("Таблицы базы данных созданы успешно")
        
        # Проверяем, есть ли категории, и добавляем их если нет
        if not Category.query.first():
            from avito_ads.services.avito_service import AvitoService
            avito_service = AvitoService()
            
            # Добавляем категории из предустановленных
            for cat in avito_service.categories:
                category = Category(id=cat['id'], name=cat['name'])
                db.session.add(category)
            
            db.session.commit()
            logger.info("Категории были успешно добавлены в базу данных")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {str(e)}")
        print(f"ОШИБКА: Не удалось инициализировать базу данных - {str(e)}")

# Регистрация маршрутов
from avito_ads.routes import main_bp
app.register_blueprint(main_bp)

# Инициализация сервисов
from avito_ads.services.avito_service import AvitoService
from avito_ads.services.scheduler import AdScheduler

# Глобальная переменная для планировщика
scheduler = None

def start_scheduler():
    """Запуск планировщика в отдельном потоке"""
    global scheduler
    try:
        with app.app_context():
            avito_service = AvitoService()
            scheduler = AdScheduler(avito_service=avito_service)
            # Добавляем планировщик в конфигурацию приложения
            app.config['SCHEDULER'] = scheduler
            scheduler.start()
            logger.info("Планировщик запущен")
    except Exception as e:
        logger.error(f"Ошибка при запуске планировщика: {str(e)}")

# Запуск приложения
if __name__ == '__main__':
    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Запускаем приложение на порту 5005
    app.run(host='127.0.0.1', debug=True, port=5005) 