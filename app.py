from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_required, current_user
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler

# Загрузка переменных окружения
load_dotenv()

# Инициализация Flask приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))

# Инициализация расширений
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Настройка логирования
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Avito Ads Manager startup')

# Импорт моделей и форм
from avito_ads.models import User, Ad, Category
from avito_ads.forms import AdForm, CategoryForm

# Маршруты
@app.route('/')
@login_required
def index():
    ads = Ad.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', ads=ads)

@app.route('/add_ad', methods=['GET', 'POST'])
@login_required
def add_ad():
    form = AdForm()
    if form.validate_on_submit():
        ad = Ad(
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            category_id=form.category_id.data,
            user_id=current_user.id,
            publication_hours=form.publication_hours.data,
            posts_per_day=form.posts_per_day.data
        )
        db.session.add(ad)
        db.session.commit()
        flash('Объявление успешно добавлено', 'success')
        return redirect(url_for('index'))
    return render_template('add_edit_ad.html', form=form)

@app.route('/edit_ad/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_ad(id):
    ad = Ad.query.get_or_404(id)
    if ad.user_id != current_user.id:
        flash('У вас нет прав для редактирования этого объявления', 'error')
        return redirect(url_for('index'))
    form = AdForm(obj=ad)
    if form.validate_on_submit():
        ad.title = form.title.data
        ad.description = form.description.data
        ad.price = form.price.data
        ad.category_id = form.category_id.data
        ad.publication_hours = form.publication_hours.data
        ad.posts_per_day = form.posts_per_day.data
        db.session.commit()
        flash('Объявление успешно обновлено', 'success')
        return redirect(url_for('index'))
    return render_template('add_edit_ad.html', form=form)

@app.route('/delete_ad/<int:id>')
@login_required
def delete_ad(id):
    ad = Ad.query.get_or_404(id)
    if ad.user_id != current_user.id:
        flash('У вас нет прав для удаления этого объявления', 'error')
        return redirect(url_for('index'))
    db.session.delete(ad)
    db.session.commit()
    flash('Объявление успешно удалено', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', False)) 