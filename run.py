from avito_ads import create_app
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        # Создаем приложение
        app = create_app()
        
        # Запускаем приложение
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=True
        )
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {str(e)}")
        raise 