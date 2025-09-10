from pathlib import Path
import environ, os, smtplib, ssl, certifi

env = environ.Env(
    DEBUG=(bool, True)
)

BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')

DEBUG = env('DEBUG')

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'listings',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
    # 'django_celery_results',
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

ROOT_URLCONF = 'alx_travel_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'alx_travel_app.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': env('ENGINE'),
        'NAME': env('NAME'),
        'USER': env('USER'),
        'PASSWORD': env('PASSWORD'),
        'HOST': env('HOST'),
        'PORT': env('PORT'),
    }
}

# Force SSL certificate verification
ssl_context = ssl.create_default_context(cafile=certifi.where())
smtplib.SMTP_SSL.context = ssl_context

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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'listings.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Email configuration

EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_USE_SSL = bool(env('EMAIL_USE_SSL'))
EMAIL_USE_TLS = bool(env('EMAIL_USE_TLS'))
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

# Celery + Redis configuration
CELERY_BROKER_URL = f"{env('REDIS_URL')}/0"
CELERY_RESULT_BACKEND = f"{env('REDIS_URL')}/1"
CELERY_TASK_ALWAYS_EAGER = bool(env('CELERY_TASK_ALWAYS_EAGER'))
CELERY_TASK_TIME_LIMIT = int(env('CELERY_TASK_TIME_LIMIT'))
CELERY_TASK_SOFT_TIME_LIMIT = int(env('CELERY_TASK_SOFT_TIME_LIMIT'))
CELERY_TASK_ACKS_LATE = bool(env('CELERY_TASK_ACKS_LATE'))
CELERY_TASK_REJECT_ON_WORKER_LOST = bool('CELERY_TASK_REJECT_ON_WORKER_LOST ')
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = bool('CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP')

# Caching settings
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"{env('REDIS_URL')}",
        "TIMEOUT": None,   # cache forever by default
    }
}