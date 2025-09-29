from pathlib import Path
from decouple import config
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Determine if running in Docker. Assumes DOCKER=true or DOCKER=false in .env
IS_DOCKER = config('DOCKER', default=False, cast=bool)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS
# Reads from ALLOWED_HOSTS environment variable (comma-separated string).
# e.g., ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"
# If DEBUG is True, 'localhost', '127.0.0.1', '[::1]' are added for convenience if not already present.
_allowed_hosts_env = config('ALLOWED_HOSTS', default=None)
if _allowed_hosts_env:
    ALLOWED_HOSTS = [host.strip() for host in _allowed_hosts_env.split(',') if host.strip()]
else:
    ALLOWED_HOSTS = []

if DEBUG:
    development_hosts = ['localhost', '127.0.0.1', '[::1]']
    for host in development_hosts:
        if host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)
    if not ALLOWED_HOSTS: # If env was empty and we are in debug
        ALLOWED_HOSTS = development_hosts[:]
ALLOWED_HOSTS = [host for host in ALLOWED_HOSTS if host] # Clean up any potential empty strings


# Application definition

INSTALLED_APPS = [
    'Accounts',
    'wholesale',
    'tours',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_celery_results',
    'django_celery_beat',
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

ROOT_URLCONF = 'Core.urls'

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

WSGI_APPLICATION = 'Core.wsgi.application'

# Authenticated by email
AUTH_USER_MODEL = 'Accounts.Account'

# Database
if IS_DOCKER:
    db_settings = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'), # Must be set in .env if IS_DOCKER
        'USER': config('DB_USER'), # Must be set in .env if IS_DOCKER
        'PASSWORD': config('DB_PASS'), # Must be set in .env if IS_DOCKER
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
    }
else:
    # Local development (not Docker)
    db_settings = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

# Update DATABASES settings
DATABASES = {
    'default': db_settings,
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Example for project-level static files (not belonging to a specific app)
# STATICFILES_DIRS = [
#     BASE_DIR / "static",
# ]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CELERY SETTINGS
REDIS_HOST = 'redis' if IS_DOCKER else '127.0.0.1'
REDIS_PORT = '6379' # Standard Redis port

# Default broker URL, can be overridden by CELERY_BROKER_URL in .env
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default=f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# CACHES
# Default cache location URL, can be overridden by CACHE_LOCATION_URL in .env
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('CACHE_LOCATION_URL', default=f'redis://{REDIS_HOST}:{REDIS_PORT}/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        "TIMEOUT": 60 * 15,
    }
}

# CSRF_TRUSTED_ORIGINS
# For HTTPS setups or when behind a proxy.
# e.g., CSRF_TRUSTED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
_csrf_trusted_origins_env = config('CSRF_TRUSTED_ORIGINS', default=None)
if _csrf_trusted_origins_env:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf_trusted_origins_env.split(',') if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []

if DEBUG and not any(o for o in CSRF_TRUSTED_ORIGINS if 'localhost' in o or '127.0.0.1' in o):
    # Add common local development origins if not already specified via environment variable
    CSRF_TRUSTED_ORIGINS.extend(['http://localhost:8000', 'http://127.0.0.1:8000'])
CSRF_TRUSTED_ORIGINS = [origin for origin in CSRF_TRUSTED_ORIGINS if origin] # Clean up empty strings


# LOGGING CONFIGURATION
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{asctime}] {levelname} {module} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple', # Use 'verbose' for more detailed logs
        },
    },
    'root': {
        'handlers': ['console'],
        'level': config('DJANGO_ROOT_LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        # Example for your 'wholesale' app logger:
        'wholesale': {
            'handlers': ['console'],
            'level': config('APP_WHOLESALE_LOG_LEVEL', default='DEBUG' if DEBUG else 'INFO'),
            'propagate': True, # Set to False if you don't want 'wholesale' logs to also go to root
        },
        # Add other app-specific or library-specific loggers here
        # 'celery': {
        #     'handlers': ['console'],
        #     'level': config('CELERY_LOG_LEVEL', default='INFO'),
        #     'propagate': True,
        # },
    },
}
