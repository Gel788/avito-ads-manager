import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from avito_ads.models.ad_model import Ad
from avito_ads.services.avito_service import AvitoService
from avito_ads.config.config import Config
from avito_ads import db
import json
from flask import current_app

logger = logging.getLogger(__name__)

class AdScheduler:
    def __init__(self, avito_service=None):
        self.scheduler = BackgroundScheduler()
        self.avito_service = avito_service or AvitoService()
        self.check_interval = Config.SCHEDULER_CHECK_INTERVAL
        self.scheduler.add_job(self.check_ads, 'interval', minutes=self.check_interval)
        logging.info(f"Планировщик инициализирован с интервалом {self.check_interval} минут")
        self.scheduler.start()
    
    def start(self):
        """Запуск планировщика"""
        if not self.scheduler.running:
            self.scheduler.start()
            logging.info("Планировщик запущен")
        else:
            logging.info("Планировщик уже запущен")
    
    def stop(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()
        logging.info("Планировщик остановлен")
    
    def check_ads(self):
        """Проверка объявлений для публикации"""
        try:
            if not current_app:
                logger.error("Нет активного контекста приложения")
                return
                
            with current_app.app_context():
                now = datetime.now()
                ads = Ad.query.filter(
                    Ad.is_active == True,
                    Ad.schedule_start <= now,
                    Ad.schedule_end >= now
                ).all()
                
                for ad in ads:
                    self._process_ad(ad)
        except Exception as e:
            logger.error(f"Ошибка при проверке объявлений: {str(e)}")
    
    def _process_ad(self, ad):
        """Обработка отдельного объявления"""
        try:
            now = datetime.now()
            today = now.date()
            
            # Получаем время публикации из JSON
            try:
                publication_hours = json.loads(ad.publication_hours) if ad.publication_hours else []
            except:
                publication_hours = []
                
            repost_count = ad.repost_times or 1
            
            # Проверяем, нужно ли публиковать в текущий час
            current_hour = now.hour
            if current_hour in publication_hours[:repost_count]:
                # Проверяем, не публиковали ли мы уже сегодня
                last_publication = ad.last_publication
                if not last_publication or last_publication.date() < today:
                    self._publish_ad(ad)
        except Exception as e:
            logging.error(f"Ошибка при обработке объявления {ad.id}: {str(e)}")
    
    def _publish_ad(self, ad):
        """Публикация объявления"""
        try:
            # Проверяем, существует ли объявление
            if not ad or not hasattr(ad, 'id'):
                logger.warning("Попытка публикации несуществующего объявления")
                return
            
            # Проверяем состояние объявления
            with db.session.begin():
                try:
                    # Попытка получить объявление из базы данных (проверка существования)
                    if isinstance(ad, int):
                        # Если передан ID, получаем объект объявления
                        from avito_ads.models.ad_model import Ad
                        ad_obj = Ad.query.get(ad)
                        if not ad_obj:
                            logger.warning(f"Объявление с ID {ad} не найдено в базе данных")
                            return
                        ad = ad_obj
                    
                    if not ad.is_active:
                        logger.info(f"Объявление {ad.id} неактивно, пропускаем публикацию")
                        return
                    
                    # Проверяем, что текущая дата входит в период публикации
                    today = datetime.now().date()
                    if not (ad.schedule_start <= today <= ad.schedule_end):
                        logger.info(f"Дата публикации {today} вне периода {ad.schedule_start} - {ad.schedule_end}")
                        return
                    
                    # Подготавливаем данные для публикации
                    ad_data = {
                        'title': ad.title,
                        'description': ad.description,
                        'price': float(ad.price),
                        'address': ad.address,
                        'manager_name': ad.manager_name,
                        'contact_phone': ad.contact_phone,
                        'allow_email': ad.allow_email,
                        'category_id': ad.categories[0].avito_id if ad.categories else None,
                        'photos': ad.photo_paths if ad.photo_paths else []
                    }
                    
                    # Публикуем объявление
                    if ad.avito_id:
                        result = self.avito_service.update_ad(ad.avito_id, ad_data)
                    else:
                        result = self.avito_service.create_ad(ad_data)
                        if result and 'id' in result:
                            ad.avito_id = result['id']
                    
                    # Обновляем время последней публикации
                    ad.last_publication = datetime.now()
                    db.session.commit()
                    
                    logger.info(f"Объявление {ad.id} успешно опубликовано")
                except Exception as db_error:
                    logger.error(f"Ошибка базы данных при публикации объявления: {str(db_error)}")
        except Exception as e:
            logger.error(f"Ошибка при публикации объявления: {str(e)}")
    
    def schedule_ad(self, ad):
        """Планирование публикации объявления"""
        try:
            # Получаем часы публикации
            try:
                publication_hours = json.loads(ad.publication_hours) if ad.publication_hours else []
            except:
                publication_hours = []
                
            # Удаляем существующие задания для этого объявления
            self.unschedule_ad(ad.id)
            
            # Создаем новые задания для каждого времени публикации
            for hour in publication_hours:
                trigger = CronTrigger(
                    day_of_week='*',
                    hour=hour,
                    minute=0
                )
                
                self.scheduler.add_job(
                    self._publish_ad,
                    trigger=trigger,
                    args=[ad],
                    id=f'ad_{ad.id}_hour_{hour}',
                    replace_existing=True
                )
            
            logger.info(f"Объявление {ad.id} запланировано на публикацию")
        except Exception as e:
            logger.error(f"Ошибка при планировании объявления {ad.id}: {str(e)}")
    
    def unschedule_ad(self, ad_id):
        """Удаление заданий публикации для объявления"""
        try:
            # Проверяем, запущен ли планировщик
            if not self.scheduler or not hasattr(self.scheduler, 'running') or not self.scheduler.running:
                logger.warning(f"Планировщик не запущен при попытке удалить задания для объявления {ad_id}")
                return True
            
            # Префикс для идентификации заданий
            job_prefix = f'ad_{ad_id}_hour_'
            removed_count = 0
            
            # Получаем список всех заданий
            try:
                jobs = self.scheduler.get_jobs()
            except Exception as e:
                logger.error(f"Ошибка при получении списка заданий: {str(e)}")
                return True  # Возвращаем True, чтобы не блокировать удаление объявления
            
            # Удаляем каждое задание, относящееся к объявлению
            for job in jobs:
                try:
                    if hasattr(job, 'id') and job.id and job.id.startswith(job_prefix):
                        job.remove()
                        removed_count += 1
                except Exception as job_error:
                    logger.error(f"Ошибка при удалении задания {job.id}: {str(job_error)}")
            
            logger.info(f"Удалено {removed_count} заданий публикации для объявления {ad_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении заданий для объявления {ad_id}: {str(e)}")
            return True  # Возвращаем True, чтобы не блокировать удаление объявления
    
    def update_schedule(self, ad):
        """Обновление расписания публикации"""
        self.schedule_ad(ad)
    
    def add_ad_to_schedule(self, ad):
        """Добавление объявления в расписание"""
        try:
            if not ad.is_active:
                logger.info(f"Объявление {ad.id} не активно, не добавляем в расписание")
                return False
            
            if not ad.get_hours_array():
                logger.warning(f"Объявление {ad.id} не имеет часов публикации, не добавляем в расписание")
                return False
            
            # Устанавливаем флаг is_published в False при добавлении в расписание
            ad.is_published = False
            db.session.commit()
            
            logger.info(f"Объявление {ad.id} добавлено в расписание, часы публикации: {ad.get_hours_array()}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении объявления {ad.id} в расписание: {str(e)}")
            return False
    
    def remove_ad_from_schedule(self, ad_id):
        """Удаление объявления из расписания"""
        try:
            # Находим объявление в базе данных
            ad = Ad.query.get(ad_id)
            
            if not ad:
                logger.warning(f"Объявление с ID {ad_id} не найдено в базе данных")
                return False
            
            # Пометить объявление как неактивное
            ad.is_active = False
            db.session.commit()
            
            logger.info(f"Объявление {ad_id} успешно удалено из расписания")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении объявления {ad_id} из расписания: {str(e)}")
            return False 