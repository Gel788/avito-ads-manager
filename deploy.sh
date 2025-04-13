#!/bin/bash

# Установка зависимостей
pip install -r requirements.txt

# Создание базы данных через API Render
curl -X POST https://api.render.com/v1/databases \
  -H "Authorization: Bearer rnd_OJ6WmIU7AKQi8zCGiQZYMVkGIJzN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "avito-db",
    "database": "avito_ads",
    "user": "avito_user",
    "plan": "free",
    "region": "ohio"
  }'

# Создание веб-сервиса через API Render
curl -X POST https://api.render.com/v1/services \
  -H "Authorization: Bearer rnd_OJ6WmIU7AKQi8zCGiQZYMVkGIJzN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "web",
    "name": "avito-ads",
    "env": "python",
    "region": "ohio",
    "plan": "free",
    "buildCommand": "pip install -r requirements.txt && python init_db.py",
    "startCommand": "gunicorn run:app",
    "healthCheckPath": "/",
    "autoDeploy": true,
    "repo": "https://github.com/Gel788/avito-ads-manager.git",
    "branch": "main",
    "envVars": {
      "DATABASE_URL": "postgresql://avito_user:postgres@localhost:5432/avito_ads",
      "SECRET_KEY": "your-secret-key",
      "FLASK_ENV": "production",
      "FLASK_DEBUG": "0",
      "AVITO_CLIENT_ID": "your-client-id",
      "AVITO_CLIENT_SECRET": "your-client-secret",
      "AVITO_ACCESS_TOKEN": "your-access-token"
    }
  }' 