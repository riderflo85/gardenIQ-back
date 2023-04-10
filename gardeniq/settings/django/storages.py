"""Setting for Django Storage (for local storage)"""
from gardeniq.settings.django.paths import DJANGO_ROOT_DIR


# https://docs.djangoproject.com/fr/4.1/ref/settings/#media-url
MEDIA_URL = 'media/'

# https://docs.djangoproject.com/fr/4.1/ref/settings/#media-root
MEDIA_ROOT = DJANGO_ROOT_DIR / 'media'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/
# https://docs.djangoproject.com/fr/4.1/ref/settings/#static-url
STATIC_URL = 'static/'

# https://docs.djangoproject.com/fr/4.1/ref/settings/#static-root
STATIC_ROOT = DJANGO_ROOT_DIR / 'staticfiles'

# https://docs.djangoproject.com/fr/4.1/ref/settings/#staticfiles-dirs
STATICFILES_DIRS = [DJANGO_ROOT_DIR / 'static']
