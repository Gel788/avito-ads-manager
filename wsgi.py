import os
import sys

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from avito_ads.app import app

if __name__ == "__main__":
    app.run() 