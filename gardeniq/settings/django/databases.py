"""Settings for Django Databases"""
from gardeniq.settings import get_config_value
from gardeniq.settings.django.paths import PROJECT_ROOT_DIR

ENGINES = {
    'sqlite3': 'django.db.backends.sqlite3',
    'postgresql': 'django.db.backends.postgresql'
}

_SQL_ENGINE = get_config_value('SQL_ENGINE')

# https://docs.djangoproject.com/en/4.1/ref/settings/#databases
if _SQL_ENGINE == 'sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': ENGINES[_SQL_ENGINE],
            'NAME': PROJECT_ROOT_DIR / get_config_value('SQL_NAME', default='gardeniq.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': ENGINES[_SQL_ENGINE],
            'NAME': get_config_value('SQL_NAME'),
            'USER': get_config_value('SQL_USER'),
            'PASSWORD': get_config_value('SQL_PASSWORD'),
            'HOST': get_config_value('SQL_HOST'),
            'PORT': get_config_value('SQL_PORT'),
        }
    }

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
