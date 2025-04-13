# Avito Ads Manager

Система для управления и автоматизации публикации объявлений на площадке Avito.

## Описание

Приложение предоставляет пользователям возможность автоматизировать работу с объявлениями на Avito:
- Создание и редактирование объявлений
- Управление категориями
- Загрузка нескольких фотографий
- Планирование публикаций по расписанию
- Автоматический репост объявлений

## Технологии

- Python 3.9+
- Flask
- SQLAlchemy
- SQLite
- Bootstrap 4
- APScheduler для планирования задач
- Avito API

## Установка и запуск

### Предварительные требования

- Python 3.9 или выше
- pip

### Шаги установки

1. Клонировать репозиторий
```bash
git clone https://github.com/albertgiloan/avito-ads-manager.git
cd avito-ads-manager
```

2. Установить зависимости
```bash
pip install -r requirements.txt
```

3. Настройка окружения
```bash
cp .env.example .env
# Отредактируйте .env файл, добавив ваши учетные данные API Avito
```

4. Подготовка базы данных
```bash
mkdir -p instance
touch instance/avito_db.sqlite3
chmod 777 instance/avito_db.sqlite3
```

5. Запуск приложения
```bash
python -m avito_ads.app
```

## Использование

После запуска приложение будет доступно по адресу http://localhost:5005

## Автор

Гилоян Альберт

## Лицензия

MIT 