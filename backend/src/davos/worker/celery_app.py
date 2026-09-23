from davos.platform.settings.app_settings import AppSettings
from davos.worker.celery_app_factory import CeleryAppFactory

celery_app = CeleryAppFactory.create(AppSettings())
