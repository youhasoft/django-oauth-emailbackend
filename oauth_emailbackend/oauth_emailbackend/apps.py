from typing import OrderedDict
from django.apps import AppConfig
from django.conf import settings
import importlib

class OAuthEmailBackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'oauth_emailbackend'
    providers = None

    class Meta:
        prefix = 'OAUTH_EMAIL'

    # TASK_CONFIG = {}
    # BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # CHUNK_SIZE = 10
    # MESSAGE_EXTRA_ATTRIBUTES = None

    def ready(self) -> None:
        # load providers 
        _providers = getattr(settings, 'OAUTH_EMAILBACKEND_PROVIDERS', [])
        
        providers = OrderedDict()
        for module_path in _providers:
            mod = importlib.import_module(module_path)
            instance = mod.OAuthProvider()
            providers[instance.provider_key] = instance

        self.providers = providers

        return super().ready()