"""
Settings for Django Authentication

Note: See :mod:`gardeniq/settings/third_party/rest_framework` for API authentication.
"""

from datetime import timedelta

# https://docs.djangoproject.com/fr/4.1/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

# https://docs.djangoproject.com/fr/4.1/ref/settings/#auth-user-model
# AUTH_USER_MODEL = 'auth.User'

# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# https://docs.djangoproject.com/fr/4.1/ref/settings/#password-reset-timeout
PASSWORD_RESET_TIMEOUT = int(timedelta(days=1).total_seconds())

# https://docs.djangoproject.com/fr/4.1/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
