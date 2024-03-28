from typing import OrderedDict
from django.apps import AppConfig
from django.conf import settings
import importlib

from celery.exceptions import ImproperlyConfigured

class OAuthEmailBackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'oauth_emailbackend'
    providers = None
    use_celery = False

    class Meta:
        prefix = 'OAUTH_EMAIL'

    # TASK_CONFIG = {}
    # BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # CHUNK_SIZE = 10
    # MESSAGE_EXTRA_ATTRIBUTES = None

    def ready(self) -> None:
        # load providers 
        _providers = getattr(settings, 'OAUTH_EMAILBACKEND_PROVIDERS', [])
        _use_celery = getattr(settings, 'OAUTH_EMAILBACKEND_USE_CELERY', False)

        # EMAIL_BACKEND기 `OAuthCeleryEmailBackend`인 경우 Celery 설정을 확인한다.
        if _use_celery:
            celery_broker_url = getattr(settings, 'CELERY_BROKER_URL', None)
            if not celery_broker_url:
                """`OAuthCeleryEmailBackend`를 사용하는 경우 settings.py에 `CELERY_BROKER_URL`를 설정하여야 합니다."""
                raise ImproperlyConfigured('''[oauth_emailbackend] 
                                           When using `OAuthCeleryEmailBackend`, `CELERY_BROKER_URL` must be set in settings.py.
                                           ''')
        self.use_celery = _use_celery
        
        providers = OrderedDict()
        for module_path in _providers:
            mod = importlib.import_module(module_path)
            klass = mod.OAuthProvider
            providers[klass.provider_key] = klass

        self.providers = providers

        return super().ready()