#!/bin/bash

# Этот скрипт загружает код в GitHub репозиторий

# Загрузка переменных окружения
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Файл .env не найден"
    exit 1
fi

# Проверка наличия переменных окружения
if [ -z "$GITHUB_TOKEN" ] || [ -z "$GITHUB_USERNAME" ] || [ -z "$GITHUB_REPO" ]; then
    echo "Не все необходимые переменные окружения установлены в .env"
    exit 1
fi

BRANCH="main"

# Проверка наличия git
if ! command -v git &> /dev/null; then
    echo "Git не установлен. Пожалуйста, установите git"
    exit 1
fi

# Проверка инициализации git
if [ ! -d .git ]; then
    echo "Инициализация git репозитория..."
    git init
fi

# Создание .gitignore если его нет
if [ ! -f .gitignore ]; then
    echo "Создание .gitignore..."
    cat > .gitignore << EOL
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
.env
instance/
.webassets-cache
.env
.venv
venv/
ENV/
.DS_Store
uploads/
*.sqlite3
logs/
EOL
fi

# Настройка Git
git config user.name "Albert Giloyan"
git config user.email "albertgiloan@gmail.com"

# Добавление всех файлов в git
echo "Добавление файлов в git..."
git add .

# Создание коммита
echo "Создание коммита..."
git commit -m "Инициализация проекта Avito Ads Manager"

# Удаление текущего remote если существует
git remote remove origin 2>/dev/null

# Добавление нового remote
echo "Настройка подключения к GitHub..."
git remote add origin https://$GITHUB_TOKEN@github.com/$GITHUB_USERNAME/$GITHUB_REPO.git

# Создание и переключение на main ветку если её нет
if ! git rev-parse --verify $BRANCH &>/dev/null; then
    git checkout -b $BRANCH
fi

# Отправка кода
echo "Отправка кода в GitHub..."
if git push -u origin $BRANCH --force; then
    echo "✅ Код успешно загружен в репозиторий $GITHUB_REPO"
    echo "🌐 Репозиторий доступен по адресу: https://github.com/$GITHUB_USERNAME/$GITHUB_REPO"
else
    echo "❌ Ошибка при загрузке кода"
    exit 1
fi 