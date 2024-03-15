"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 5.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-a#)$5ey7n$5)ad82=e*v=33la)smlg*mq6$&oibj!6riki!r(7'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

SITE_ID = 1

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Add sites app
    'django.contrib.sites',
    # 'oauth_emailbackend.emailbackend',
    'oauth_emailbackend',

    # Used for callback test.
    # python manage.py runsslserver 0.0.0.0:8443  
    "sslserver",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'ko-KR'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'
# STATICFILES_DIRS = [
#    BASE_DIR / "static",
# ]


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


#----- django-oauth-emailbackend settings -----#
EMAIL_BACKEND = 'oauth_emailbackend.emailbackend.backends.OAuthEmailBackend' # OAuthCeleryEmailBackend
OAUTH_EMAILBACKEND_DBNAME = 'default'
OAUTH_EMAILBACKEND_PROVIDERS = (
    'oauth_emailbackend.providers.gmail',
)
# 콜백 도메인을 현재 사이트 도메인과 다르게 지정하려면 설정. Host with scheme 예) https://domain.to
OAUTH_EMAILBACKEND_CALLBACK_HOST = None

# https://console.cloud.google.com에서 API 생성 - OAuth 동의화면 구성 - 사용자 인증 정보 만들기 
# 클라이언트 아이디 & 보안 비밀번호
# OAUTH_EMAILBACKEND_GMAIL_CLIENT_ID = '831886363443-r9717rve6kqpf2pbut5l42u8b9fso3ir.apps.googleusercontent.com'
# OAUTH_EMAILBACKEND_GMAIL_CLIENT_SECRET = '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' 
# # 인증 후 콜백주소 
# OAUTH_EMAILBACKEND_GMAIL_CALLBACK = 'https://dev.youhasoft.com:8443/oauth_emailbackend/oauth2callback/gmail'

#----- celery settings -----#