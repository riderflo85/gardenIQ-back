"""
Settings for Django Internationalization

Note: see _Django Internationalization: https://docs.djangoproject.com/en/4.1/topics/i18n/
"""
from django.utils.translation import gettext_lazy as _

from gardeniq.settings.django.paths import DJANGO_ROOT_DIR


# https://docs.djangoproject.com/fr/4.1/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'

# https://docs.djangoproject.com/fr/4.1/ref/settings/#time-zone
TIME_ZONE = 'UTC'

# https://docs.djangoproject.com/fr/4.1/ref/settings/#use-i18n
USE_I18N = True

# https://docs.djangoproject.com/fr/4.1/ref/settings/#use-l10n
USE_L10N = True

# https://docs.djangoproject.com/fr/4.1/ref/settings/#use-tz
USE_TZ = True

# https://docs.djangoproject.com/fr/4.1/ref/settings/#locale-paths
LOCALE_PATHS = (DJANGO_ROOT_DIR / 'locale',)

# https://docs.djangoproject.com/fr/4.1/ref/settings/#languages
LANGUAGES = [
    ('en', _('English')),
    ('fr', _('French')),
]
