from pathlib import Path
import environ, os, smtplib, ssl, certifi

env = environ.Env(
    DEBUG=(bool, False)
)

BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')

DEBUG = env('DEBUG')
if DEBUG:
    ALLOWED_HOSTS = []
else:
    ALLOWED_HOSTS = [env('PROD_ALLOWED_HOSTS')]

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
    'listings.utils.middleware.IPTrackingMiddleware',
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

# Rest framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # 'EXCEPTION_HANDLER': 'listings.utils.exception_handler.custom_exception_handler'
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

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Property App",
    "DESCRIPTION": "API documentation",
    "VERSION": "1.0.0",

    "SERVERS": [{"url": "/"}],

    "SECURITY": [
        {"TokenAuth": []},
    ],

    "SECURITY_SCHEMES": {
        "TokenAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "Token",
            "description": "Token-based authentication. Enter only the token value, Swagger will add the 'Token' prefix automatically.",
        },
    },
}

# Logging configuration

LOG_DIR = os.path.join(BASE_DIR, "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # keep Django’s default loggers

    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {module}.{funcName}:{lineno} - {message}",
            "style": "{",
        },
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "django_debug.log",   # log file in project root
            "formatter": "verbose",
        },
    },

    "root": {  # root logger
        "handlers": ["console", "file"],
        "level": "INFO",
    },

    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "listings": {  
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Security Header settings for production
if not DEBUG:
    # Force HTTPS everywhere
    SECURE_SSL_REDIRECT = True  

    # Tell browsers "only use HTTPS for this site"
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Basic browser protections
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

    # Content Security Policy (limits where resources can load from)
    CSP_DEFAULT_SRC = ("'self'",)
    CSP_STYLE_SRC = ("'self'", "'unsafe-inline'",)
    CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'",)
    CSP_IMG_SRC = ("'self'", "data:", "https:")
    CSP_FONT_SRC = ("'self'", "https:", "data:")
    CSP_CONNECT_SRC = ("'self'", "https:")

# CORS (if you use APIs)
# CORS_ALLOWED_ORIGINS = [
#     "https://frontend.com",
# ]