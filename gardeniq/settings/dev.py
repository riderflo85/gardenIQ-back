from .base import *

INSTALLED_APPS += ["django_extensions"]

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] += [
    "rest_framework.authentication.SessionAuthentication",  # For swagger UI
]
