"""Settings for Django Core"""

from gardeniq.settings import get_config_value
from gardeniq.settings import to_bool
from gardeniq.settings import to_list

# https://docs.djangoproject.com/fr/4.1/ref/settings/#allowed-hosts
ALLOWED_HOSTS = get_config_value("DJANGO_ALLOWED_HOSTS", cast=to_list)

# https://docs.djangoproject.com/fr/4.1/ref/settings/#debug
DEBUG = get_config_value("DJANGO_DEBUG", default="False", cast=to_bool)

# https://docs.djangoproject.com/fr/4.1/ref/settings/#secret-key
SECRET_KEY = get_config_value("DJANGO_SECRET_KEY")

# https://docs.djangoproject.com/fr/4.1/ref/settings/#root-urlconf
ROOT_URLCONF = "gardeniq.urls"

# https://docs.djangoproject.com/fr/4.1/ref/settings/#wsgi-application
WSGI_APPLICATION = "gardeniq.wsgi.application"

ASGI_APPLICATION = "gardeniq.asgi.application"
