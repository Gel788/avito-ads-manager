import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from avito_ads.models.ad_model import Ad, db
from avito_ads.services.avito_service import AvitoService

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, app):
        self.app = app
        self.scheduler = BackgroundScheduler()
        self.avito_service = AvitoService()
        
    def init_scheduler(self):
        """Инициализация планировщика"""
        try:
            interval = int(self.app.config.get('SCHEDULER_INTERVAL', 5))
            self.scheduler.add_job(
                self.check_and_publish_ads,
                trigger=IntervalTrigger(minutes=interval),
                id='publish_ads',
                replace_existing=True
            )
            self.scheduler.start()
            logger.info(f"Планировщик инициализирован с интервалом {interval} минут")
        except Exception as e:
            logger.error(f"Ошибка при инициализации планировщика: {str(e)}")
            
    def check_and_publish_ads(self):
        """Проверка и публикация объявлений"""
        try:
            with self.app.app_context():
                current_time = datetime.now()
                ads_to_publish = Ad.query.filter(
                    Ad.is_active == True,
                    Ad.next_publication_time <= current_time
                ).all()
                
                for ad in ads_to_publish:
                    try:
                        self.avito_service.publish_ad(ad)
                        ad.last_post_date = current_time
                        ad.next_publication_time = self.calculate_next_publication_time(ad)
                        db.session.commit()
                    except Exception as e:
                        logger.error(f"Ошибка при публикации объявления {ad.id}: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error(f"Ошибка при проверке объявлений: {str(e)}")
            
    def calculate_next_publication_time(self, ad):
        """Расчет времени следующей публикации"""
        current_time = datetime.now()
        publication_hours = ad.publication_hours
        
        if not publication_hours:
            return current_time + timedelta(days=1)
            
        current_hour = current_time.hour
        next_hour = None
        
        for hour in sorted(publication_hours):
            if hour > current_hour:
                next_hour = hour
                break
                
        if next_hour is None:
            next_hour = publication_hours[0]
            return current_time.replace(hour=next_hour, minute=0, second=0) + timedelta(days=1)
            
        return current_time.replace(hour=next_hour, minute=0, second=0) 