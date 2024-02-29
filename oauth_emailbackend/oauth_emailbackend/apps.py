from django.apps import AppConfig


class OAuthEmailBackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'oauth_emailbackend'

    class Meta:
        prefix = 'OAUTH_EMAIL'

    TASK_CONFIG = {}
    BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    CHUNK_SIZE = 10
    MESSAGE_EXTRA_ATTRIBUTES = None