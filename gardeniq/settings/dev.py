from .base import *
from .third_party.spectacular import *

INSTALLED_APPS += ["django_extensions"]

# REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] += [
#     "rest_framework.authentication.SessionAuthentication",  # For swagger UI
# ]
