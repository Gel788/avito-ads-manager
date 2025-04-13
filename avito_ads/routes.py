from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from avito_ads.models.ad_model import Ad, Category, db
from avito_ads.forms import AdForm
from avito_ads.services.avito_service import AvitoService
from avito_ads.services.scheduler import AdScheduler
import logging
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid
from flask_login import login_required
from avito_ads.config.config import Config
import json
from sqlalchemy import text

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)
avito_service = AvitoService()

def allowed_file(filename):
    """Проверка расширения файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@main_bp.route('/')
def index():
    """Главная страница со списком объявлений"""
    try:
        with current_app.app_context():
            ads = Ad.query.order_by(Ad.created_at.desc()).all()
        return render_template('index.html', ads=ads)
    except Exception as e:
        logger.error(f"Ошибка при загрузке объявлений: {str(e)}")
        flash(f'Ошибка при загрузке объявлений: {str(e)}', 'error')
        return render_template('index.html', ads=[])

@main_bp.route('/add', methods=['GET', 'POST'])
def add_ad():
    """Добавление нового объявления"""
    form = AdForm()
    
    if form.validate_on_submit():
        try:
            # Создание нового объявления
            new_ad = Ad(
                title=form.title.data,
                description=form.description.data,
                price=form.price.data,
                address=form.address.data,
                manager_name=form.manager_name.data,
                contact_phone=form.contact_phone.data,
                allow_email=form.allow_email.data,
                repost_times=form.repost_times.data,
                is_active=form.is_active.data,
                publication_hours=json.dumps(form.publication_hours.data),
                schedule_start=form.schedule_start.data,
                schedule_end=form.schedule_end.data
            )
            
            # Обработка загруженных фотографий
            uploaded_photos = []
            if form.photos.data:
                for photo in form.photos.data:
                    if photo and allowed_file(photo.filename):
                        # Генерируем уникальное имя файла
                        filename = secure_filename(photo.filename)
                        unique_filename = f"{uuid.uuid4()}__{filename}"
                        
                        # Создаем директорию для загрузок, если она не существует
                        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                        
                        # Сохраняем фото
                        photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                        photo.save(photo_path)
                        
                        # Добавляем путь к фото в список
                        uploaded_photos.append(unique_filename)
            
            # Устанавливаем пути к фотографиям
            new_ad.set_photos(uploaded_photos)
            
            # Добавляем выбранные категории
            selected_categories = Category.query.filter(Category.id.in_(form.categories.data)).all()
            for category in selected_categories:
                new_ad.categories.append(category)
            
            # Сохраняем объявление в базе данных
            db.session.add(new_ad)
            db.session.commit()
            
            # Если объявление активно, планируем его публикацию
            if new_ad.is_active:
                scheduler = current_app.config.get('SCHEDULER')
                if scheduler:
                    scheduler.add_ad_to_schedule(new_ad)
            
            flash('Объявление успешно добавлено!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Ошибка при добавлении объявления: {str(e)}")
            flash(f'Ошибка при добавлении объявления: {str(e)}', 'danger')
    
    # Если валидация не прошла, выводим форму с ошибками
    return render_template('add_edit_ad.html', form=form, title='Добавление объявления')

@main_bp.route('/edit/<int:ad_id>', methods=['GET', 'POST'])
def edit_ad(ad_id):
    """Редактирование объявления"""
    ad = Ad.query.get_or_404(ad_id)
    form = AdForm(obj=ad)
    
    if request.method == 'GET':
        # При GET запросе заполняем список категорий
        selected_categories = [c.id for c in ad.categories]
        form.categories.data = selected_categories
    
    if form.validate_on_submit():
        try:
            # Обновляем основные поля
            form.populate_obj(ad)
            
            # Сохраняем часы публикации
            ad.publication_hours = json.dumps(form.publication_hours.data)
            
            # Обработка фотографий - добавляем новые
            if form.photos.data and any(form.photos.data):
                for photo in form.photos.data:
                    if photo and allowed_file(photo.filename):
                        # Генерируем уникальное имя файла
                        filename = secure_filename(f"{uuid.uuid4()}_{photo.filename}")
                        # Сохраняем файл в папку загрузок
                        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        photo.save(filepath)
                        # Сохраняем относительный путь для базы данных
                        relative_path = os.path.join('uploads', filename)
                        if not ad.photo_paths:
                            ad.photo_paths = []
                        ad.photo_paths.append(relative_path)
                        logger.info(f"Загружена фотография: {relative_path}")
            
            # Обновляем категории
            ad.categories = []
            for cat_id in form.categories.data:
                category = Category.query.filter_by(id=cat_id).first()
                if category:
                    ad.categories.append(category)
            
            # Сохраняем изменения
            db.session.commit()
            
            # Обновляем расписание публикации, если объявление активно
            if ad.is_active:
                scheduler = AdScheduler(AvitoService())
                scheduler.update_schedule(ad)
            
            flash('Объявление успешно обновлено', 'success')
            return redirect(url_for('main.index'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при обновлении объявления: {str(e)}")
            flash('Произошла ошибка при обновлении объявления', 'error')
    
    return render_template('add_edit_ad.html', form=form, ad=ad, title='Редактирование объявления')

@main_bp.route('/delete/<int:ad_id>', methods=['GET', 'POST'])
def delete_ad(ad_id):
    """Удаление объявления"""
    try:
        ad = Ad.query.get_or_404(ad_id)
        
        # Сначала отключаем внешние ключи для предотвращения блокировок
        db.session.execute(text('PRAGMA foreign_keys=OFF'))
        
        # Удаляем связи с категориями
        ad.categories = []
        db.session.commit()
        
        # Сохраняем пути к файлам изображений для удаления после удаления объявления
        photo_paths = ad.get_photos()
        
        # Удаляем объявление
        db.session.delete(ad)
        db.session.commit()
        
        # Включаем обратно внешние ключи
        db.session.execute(text('PRAGMA foreign_keys=ON'))
        
        # Удаляем файлы изображений
        for photo in photo_paths:
            try:
                full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    logger.info(f"Удалено изображение: {full_path}")
            except Exception as e:
                logger.error(f"Ошибка при удалении изображения {photo}: {str(e)}")
        
        # Удаляем объявление из планировщика
        scheduler = current_app.config.get('SCHEDULER')
        if scheduler:
            try:
                scheduler.remove_ad_from_schedule(ad_id)
                logger.info(f"Объявление {ad_id} удалено из планировщика")
            except Exception as e:
                logger.error(f"Ошибка при удалении объявления {ad_id} из планировщика: {str(e)}")
        
        flash('Объявление успешно удалено!', 'success')
        return redirect(url_for('main.index'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении объявления {ad_id}: {str(e)}")
        flash(f'Ошибка при удалении объявления: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/categories')
def get_categories():
    """Получение списка категорий"""
    try:
        categories = avito_service.get_categories()
        return jsonify(categories)
    except Exception as e:
        logger.error(f"Ошибка при получении категорий: {str(e)}")
        return jsonify({'error': 'Не удалось получить список категорий'}), 500

@main_bp.route('/ad/<int:ad_id>')
def ad_detail(ad_id):
    """Просмотр детальной страницы объявления"""
    try:
        ad = Ad.query.get_or_404(ad_id)
        return render_template('ad_detail.html', ad=ad)
    except Exception as e:
        logger.error(f"Ошибка при просмотре объявления: {str(e)}")
        flash('Произошла ошибка при загрузке объявления', 'error')
        return redirect(url_for('main.index')) 