import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class Config:
    """Конфигурация приложения"""
    
    # Базовые настройки
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-please-change')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Настройки базы данных
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    INSTANCE_PATH = os.path.join(BASE_DIR, 'instance')
    if not os.path.exists(INSTANCE_PATH):
        os.makedirs(INSTANCE_PATH, mode=0o777, exist_ok=True)
    
    # Получаем URL базы данных
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Если это Render.com (PostgreSQL)
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')
    
    # Если нет URL базы данных, используем SQLite
    if not DATABASE_URL:
        DB_FILE = os.path.join(BASE_DIR, 'avito_database.sqlite3')
        try:
            if os.path.exists(DB_FILE):
                os.chmod(DB_FILE, 0o777)  # Полные права доступа
        except Exception as e:
            print(f"Ошибка при установке прав доступа для базы данных: {str(e)}")
        DATABASE_URL = 'sqlite:///' + DB_FILE
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки SQLite для улучшения работы с базой данных
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Проверка соединения перед использованием
        'pool_recycle': 3600,   # Переподключение каждый час
    }
    
    # Добавляем специфичные настройки для SQLite
    if DATABASE_URL and DATABASE_URL.startswith('sqlite:'):
        SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {
            'timeout': 60,  # Увеличение таймаута соединения
            'check_same_thread': False,  # Разрешить использование соединения в разных потоках
            'isolation_level': None  # Отключение автоматических транзакций для повышения производительности
        }
    
    # Настройки загрузки файлов
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'avito_ads', 'static', 'uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    
    # Настройки Avito API
    AVITO_CLIENT_ID = os.getenv('AVITO_CLIENT_ID', 'test_id')
    AVITO_CLIENT_SECRET = os.getenv('AVITO_CLIENT_SECRET', 'test_secret')
    AVITO_API_URL = 'https://api.avito.ru/autoload/v2'
    AVITO_AUTH_URL = 'https://api.avito.ru/token'
    AVITO_ACCESS_TOKEN = os.getenv('AVITO_ACCESS_TOKEN', 'test_token')
    AVITO_SCOPE = 'read write'
    
    # Настройки планировщика
    SCHEDULER_INTERVAL = int(os.getenv('SCHEDULER_INTERVAL', '5'))  # в минутах
    SCHEDULER_CHECK_INTERVAL = 5  # 5 минут
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY = 60  # 1 минута
    
    # Настройки репоста
    MAX_REPOSTS_PER_DAY = int(os.getenv('MAX_REPOSTS_PER_DAY', '10'))
    MIN_INTERVAL_BETWEEN_POSTS = int(os.getenv('MIN_INTERVAL_BETWEEN_POSTS', '1'))  # в часах
    
    # API Rate Limits
    API_RATE_LIMIT = 100
    API_RATE_LIMIT_PERIOD = 60  # секунд
    
    # Настройки логирования
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join('logs', 'avito_ads.log')
    if not os.path.exists('logs'):
        os.makedirs('logs', exist_ok=True)
    
    # Настройки XML файла
    XML_TEMPLATE_PATH = os.getenv('XML_TEMPLATE_PATH', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates', 'avito.xml'))
    
    # Ограничения файлов
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10 MB
    
    # Ad settings
    MAX_PHOTOS_PER_AD = 30
    MAX_DESCRIPTION_LENGTH = 2000
    MAX_TITLE_LENGTH = 100
    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
    MAX_REPOSTS_PER_DAY = MAX_REPOSTS_PER_DAY
    MIN_REPOST_INTERVAL = MIN_INTERVAL_BETWEEN_POSTS * 3600  # перевод часов в секунды 