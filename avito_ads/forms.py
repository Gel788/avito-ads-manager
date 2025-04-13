from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import StringField, TextAreaField, DecimalField, SelectField, BooleanField, DateTimeField, IntegerField, SelectMultipleField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from datetime import datetime, timedelta
from avito_ads.config.config import Config
from avito_ads.services.avito_service import AvitoService
import logging
from avito_ads.models.ad_model import Category

class AdForm(FlaskForm):
    # Основные поля
    title = StringField('Заголовок', validators=[
        DataRequired(message='Заголовок обязателен'),
        Length(max=100)
    ])
    
    description = TextAreaField('Описание', validators=[
        DataRequired(message='Описание обязательно'),
        Length(max=2000)
    ])
    
    price = IntegerField('Цена', validators=[
        DataRequired(message='Цена обязательна')
    ])
    
    categories = SelectMultipleField('Категории (удерживайте Ctrl/Cmd для выбора нескольких)',
        coerce=int,
        validators=[DataRequired(message='Выберите хотя бы одну категорию')],
        render_kw={"size": 6}
    )
    
    address = StringField('Адрес', validators=[
        DataRequired(message='Адрес обязателен'),
        Length(max=255)
    ])
    
    manager_name = StringField('Имя менеджера', validators=[
        DataRequired(message='Имя менеджера обязательно'),
        Length(max=100)
    ])
    
    contact_phone = StringField('Телефон', validators=[
        DataRequired(message='Телефон обязателен'),
        Length(max=20)
    ])
    
    allow_email = BooleanField('Разрешить email-уведомления', default=True)
    
    photos = MultipleFileField('Фотографии (макс. 10)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Только изображения (jpg, jpeg, png)')
    ])
    
    publication_hours = SelectMultipleField('Часы публикации', choices=[(str(i), f"{i}:00") for i in range(24)], 
                                           validators=[DataRequired(message='Выберите хотя бы один час публикации')],
                                           render_kw={"size": 5})
    
    repost_times = IntegerField('Количество репостов', default=0, validators=[NumberRange(min=0, max=10)])
    
    schedule_start = DateField('Дата начала', format='%Y-%m-%d', validators=[Optional()])
    schedule_end = DateField('Дата окончания', format='%Y-%m-%d', validators=[Optional()])
    
    is_active = BooleanField('Активно', default=True)
    
    submit = SubmitField('Сохранить')
    
    def __init__(self, *args, **kwargs):
        super(AdForm, self).__init__(*args, **kwargs)
        # Получение списка категорий из базы данных
        try:
            categories = Category.query.all()
            self.categories.choices = [(c.id, c.name) for c in categories]
        except Exception as e:
            print(f"Ошибка при загрузке категорий: {str(e)}")
            self.categories.choices = []  # Установим пустой список в случае ошибки
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
            
        # Проверка полей categories
        if not self.categories.data:
            self.categories.errors.append('Выберите хотя бы одну категорию')
            return False
            
        # Исправлена проверка времени публикации, чтобы она была менее строгой
        if self.repost_times.data >= 2 and not self.publication_hours.data:
            self.publication_hours.errors.append('Выберите хотя бы один час публикации')
            return False
            
        return True 