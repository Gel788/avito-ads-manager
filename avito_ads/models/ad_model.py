from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Column, func
from flask import current_app
import os
import json

from avito_ads.database import db
from avito_ads.models.ad_category import ad_categories

class Category(db.Model):
    """Модель категории"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Ad(db.Model):
    """Модель объявления"""
    __tablename__ = 'ads'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer)
    address = db.Column(db.String(255))
    manager_name = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    allow_email = db.Column(db.Boolean, default=True)
    publication_hours = db.Column(db.String(255), default="")
    repost_times = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    is_published = db.Column(db.Boolean, default=False)
    external_id = db.Column(db.String(100), nullable=True)
    photo_paths = db.Column(db.Text, default='[]')  # Храним как JSON-строку
    schedule_start = db.Column(db.DateTime, nullable=True)
    schedule_end = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношение многие-ко-многим с категориями
    categories = db.relationship('Category', secondary=ad_categories, 
                               backref=db.backref('ads', lazy='dynamic'))
    
    def get_photos(self):
        """Получение списка путей к фотографиям"""
        try:
            return json.loads(self.photo_paths or '[]')
        except:
            return []
    
    def get_photo_urls(self):
        """Получение URL-адресов фотографий"""
        photos = self.get_photos()
        # Возвращаем корректные пути к файлам в директории uploads
        return [f"/static/uploads/{photo}" for photo in photos if photo]
        
    def get_hours_array(self):
        """Получение массива часов публикации"""
        try:
            return json.loads(self.publication_hours or '[]')
        except:
            return []
            
    def get_display_name(self):
        """Получение отображаемого названия"""
        return self.title
        
    def set_photos(self, photos):
        """Установка списка фотографий"""
        self.photo_paths = json.dumps(photos)
    
    def add_photo(self, photo_path):
        """Добавление фотографии"""
        photos = self.get_photos()
        photos.append(photo_path)
        self.set_photos(photos)
        
    def remove_photo(self, photo_path):
        """Удаление фотографии"""
        photos = self.get_photos()
        if photo_path in photos:
            photos.remove(photo_path)
            self.set_photos(photos)
            # Удаляем файл, если он существует
            try:
                full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
            except Exception as e:
                print(f"Ошибка при удалении файла {photo_path}: {e}")
                
    def to_dict(self):
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'price': self.price,
            'address': self.address,
            'manager_name': self.manager_name,
            'contact_phone': self.contact_phone,
            'allow_email': self.allow_email,
            'publication_hours': self.get_hours_array(),
            'repost_times': self.repost_times,
            'is_active': self.is_active,
            'is_published': self.is_published,
            'external_id': self.external_id,
            'photos': self.get_photos(),
            'categories': [{"id": c.id, "name": c.name} for c in self.categories],
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Ad {self.title}>' 