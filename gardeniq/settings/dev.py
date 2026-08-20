from .base import *
from .third_party.spectacular import *

INSTALLED_APPS += ["django_extensions"]

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] += [
    "knox.auth.TokenAuthentication",  # For API token authentication
    "rest_framework.authentication.SessionAuthentication",  # For swagger UI
]
