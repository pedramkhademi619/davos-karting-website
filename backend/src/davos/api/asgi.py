from davos.api.app_factory import create_app
from davos.platform.settings.app_settings import AppSettings

app = create_app(AppSettings())
