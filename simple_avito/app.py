from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import uuid

# Инициализация приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-please-change'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///avito_ads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}

# Создаем директорию для загрузки файлов
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Инициализация расширений
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Модели
class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    avito_id = db.Column(db.String(50), unique=True, nullable=True)
    
    # Связи
    parent = db.relationship('Category', remote_side=[id], backref='children')
    
    def __repr__(self):
        return f'<Category {self.name}>'

# Таблица связи многие-ко-многим для категорий
ad_category = db.Table('ad_category',
    db.Column('ad_id', db.Integer, db.ForeignKey('ads.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)

class Ad(db.Model):
    __tablename__ = 'ads'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(256), nullable=False)
    manager_name = db.Column(db.String(100), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    allow_email = db.Column(db.Boolean, default=True)
    photo_paths = db.Column(db.JSON, nullable=True)
    publication_hours = db.Column(db.JSON, nullable=True)
    repost_times = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    schedule_start = db.Column(db.Date, nullable=False)
    schedule_end = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    categories = db.relationship('Category', secondary=ad_category, backref=db.backref('ads', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Ad {self.title}>'

# Добавляем CSRF-токен в контекст шаблонов
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

def allowed_file(filename):
    """Проверка расширения файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Инициализация базы данных и создание тестовых категорий
def init_db():
    with app.app_context():
        db.create_all()
        
        # Проверяем, есть ли уже категории
        if Category.query.count() == 0:
            # Создаем основные категории
            categories = [
                Category(name='Транспорт', avito_id='1'),
                Category(name='Недвижимость', avito_id='2'),
                Category(name='Электроника', avito_id='3'),
                Category(name='Работа', avito_id='4'),
                Category(name='Услуги', avito_id='5')
            ]
            
            # Добавляем категории в базу данных
            for category in categories:
                db.session.add(category)
            
            # Сохраняем изменения
            db.session.commit()
            print("Тестовые категории успешно созданы")

# Инициализация базы данных
init_db()

# Маршруты
@app.route('/')
def index():
    """Главная страница со списком объявлений"""
    try:
        ads = Ad.query.order_by(Ad.created_at.desc()).all()
        return render_template('index.html', ads=ads)
    except Exception as e:
        flash('Ошибка при загрузке объявлений', 'error')
        return render_template('index.html', ads=[])

@app.route('/add_ad', methods=['GET', 'POST'])
def add_ad():
    """Добавление нового объявления"""
    if request.method == 'POST':
        try:
            data = request.form
            
            # Создаем новое объявление
            ad = Ad(
                title=data.get('title'),
                description=data.get('description'),
                price=float(data.get('price', 0)),
                address=data.get('address'),
                manager_name=data.get('manager_name'),
                contact_phone=data.get('contact_phone'),
                allow_email=bool(data.get('allow_email')),
                schedule_start=datetime.strptime(data.get('schedule_start'), '%Y-%m-%d').date(),
                schedule_end=datetime.strptime(data.get('schedule_end'), '%Y-%m-%d').date(),
                repost_times=int(data.get('repost_times', 1)),
                is_active=bool(data.get('is_active', True)),
                publication_hours=json.loads(data.get('publication_hours', '[]')),
                photo_paths=[]
            )
            
            # Добавляем категории
            category_ids = request.form.getlist('categories')
            for cat_id in category_ids:
                category = Category.query.get(cat_id)
                if category:
                    ad.categories.append(category)
            
            # Обрабатываем фотографии
            files = request.files.getlist('photos')
            photo_paths = []
            
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}.{filename.split('.')[-1]}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    photo_paths.append(file_path)
            
            ad.photo_paths = photo_paths
            
            # Сохраняем объявление
            db.session.add(ad)
            db.session.commit()
            
            flash('Объявление успешно добавлено!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении объявления: {str(e)}', 'error')
    
    # Получаем все категории для формы
    categories = Category.query.all()
    return render_template('add_ad.html', categories=categories)

@app.route('/edit_ad/<int:ad_id>', methods=['GET', 'POST'])
def edit_ad(ad_id):
    """Редактирование объявления"""
    ad = Ad.query.get_or_404(ad_id)
    
    if request.method == 'POST':
        try:
            data = request.form
            
            # Обновляем данные объявления
            ad.title = data.get('title')
            ad.description = data.get('description')
            ad.price = float(data.get('price', 0))
            ad.address = data.get('address')
            ad.manager_name = data.get('manager_name')
            ad.contact_phone = data.get('contact_phone')
            ad.allow_email = bool(data.get('allow_email'))
            ad.schedule_start = datetime.strptime(data.get('schedule_start'), '%Y-%m-%d').date()
            ad.schedule_end = datetime.strptime(data.get('schedule_end'), '%Y-%m-%d').date()
            ad.repost_times = int(data.get('repost_times', 1))
            ad.is_active = bool(data.get('is_active', True))
            ad.publication_hours = json.loads(data.get('publication_hours', '[]'))
            
            # Обновляем категории
            ad.categories = []
            category_ids = request.form.getlist('categories')
            for cat_id in category_ids:
                category = Category.query.get(cat_id)
                if category:
                    ad.categories.append(category)
            
            # Обрабатываем фотографии
            files = request.files.getlist('photos')
            if files and files[0].filename:
                photo_paths = []
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        unique_filename = f"{uuid.uuid4().hex}.{filename.split('.')[-1]}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file.save(file_path)
                        photo_paths.append(file_path)
                if photo_paths:
                    ad.photo_paths = photo_paths
            
            # Сохраняем изменения
            db.session.commit()
            
            flash('Объявление успешно обновлено!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении объявления: {str(e)}', 'error')
    
    # Получаем все категории для формы
    categories = Category.query.all()
    return render_template('add_ad.html', ad=ad, categories=categories)

@app.route('/delete_ad/<int:ad_id>', methods=['POST'])
def delete_ad(ad_id):
    """Удаление объявления"""
    ad = Ad.query.get_or_404(ad_id)
    
    try:
        db.session.delete(ad)
        db.session.commit()
        flash('Объявление успешно удалено!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении объявления: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """API для получения категорий"""
    categories = Category.query.all()
    result = [{'id': c.id, 'name': c.name} for c in categories]
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True) 