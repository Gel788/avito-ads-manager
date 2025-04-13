import os
import requests
import json
import logging
from datetime import datetime, timedelta
from flask import current_app
from avito_ads.config.config import Config
from avito_ads.models.ad_model import Category, db

logger = logging.getLogger(__name__)

class AvitoService:
    """Сервис для работы с API Avito"""
    
    # Предустановленные категории для локального режима
    categories = [
        {'id': 1, 'name': 'Транспорт', 'external_id': 'auto', 'parent_id': None},
        {'id': 2, 'name': 'Недвижимость', 'external_id': 'realty', 'parent_id': None},
        {'id': 3, 'name': 'Работа', 'external_id': 'job', 'parent_id': None},
        {'id': 4, 'name': 'Услуги', 'external_id': 'services', 'parent_id': None},
        {'id': 5, 'name': 'Личные вещи', 'external_id': 'personal', 'parent_id': None},
        {'id': 6, 'name': 'Для дома и дачи', 'external_id': 'home', 'parent_id': None},
        {'id': 7, 'name': 'Электроника', 'external_id': 'electronics', 'parent_id': None},
        {'id': 8, 'name': 'Хобби и отдых', 'external_id': 'hobby', 'parent_id': None},
        {'id': 9, 'name': 'Животные', 'external_id': 'animals', 'parent_id': None},
        {'id': 10, 'name': 'Бизнес и оборудование', 'external_id': 'business', 'parent_id': None},
    ]
    
    def __init__(self, client_id=None, client_secret=None):
        """Инициализация сервиса"""
        self.client_id = client_id or Config.AVITO_CLIENT_ID
        self.client_secret = client_secret or Config.AVITO_CLIENT_SECRET
        self.api_url = Config.AVITO_API_URL
        self.auth_url = Config.AVITO_AUTH_URL
        self.access_token = Config.AVITO_ACCESS_TOKEN
        self.token_expiry = None
        
        # Если работаем с реальным API (есть client_id и client_secret)
        if self.client_id != 'test_id' and self.client_secret != 'test_secret':
            self._authenticate()
        else:
            # Работаем в локальном режиме
            self.access_token = "local_mode_token"
            logger.info("Сервис запущен в локальном режиме")
    
    def _make_request(self, method, endpoint, **kwargs):
        """Выполнение запроса к API Avito"""
        url = f"{self.api_url}/{endpoint}"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        
        # Если есть файлы для загрузки, убираем Content-Type
        if 'files' in kwargs:
            headers.pop('Content-Type', None)
        
        # Если переданы дополнительные заголовки, добавляем их
        if 'headers' in kwargs:
            additional_headers = kwargs.pop('headers')
            headers.update(additional_headers)
        
        try:
            # Выполнение запроса
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=30,
                **kwargs
            )
            
            # Проверка статуса ответа
            response.raise_for_status()
            
            # Если ответ пустой, возвращаем None
            if not response.content:
                return None
                
            # Парсинг JSON-ответа
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при выполнении запроса к {url}: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"Ошибка при парсинге ответа от {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при запросе к {url}: {str(e)}")
            return None

    def init_categories(self, db_session):
        """Инициализация категорий в базе данных"""
        try:
            # Проверяем, пуста ли таблица категорий
            if Category.query.first() is None:
                for category in self.categories:
                    new_category = Category(
                        id=category['id'],
                        name=category['name'],
                        avito_id=category['external_id'],
                        parent_id=category['parent_id']
                    )
                    db_session.add(new_category)
                db_session.commit()
                logger.info("Категории успешно инициализированы в базе данных")
            else:
                logger.info("Категории уже существуют в базе данных")
        except Exception as e:
            db_session.rollback()
            logger.error(f"Ошибка при инициализации категорий: {str(e)}")
            raise

    def get_categories(self):
        """Получение списка категорий с Avito"""
        try:
            response = self._make_request("GET", "categories")
            
            if not response:
                logger.error("Пустой ответ при получении списка категорий")
                return []
            
            if 'categories' not in response:
                logger.error("В ответе от API отсутствует поле 'categories'")
                return []
            
            return response.get('categories', [])
        except Exception as e:
            logger.error(f"Ошибка при получении списка категорий: {str(e)}")
            return []
