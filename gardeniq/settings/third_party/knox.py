"""Knox settings"""
from datetime import timedelta

# https://james1345.github.io/django-rest-knox/settings/
REST_KNOX = {
    "SECURE_HASH_ALGORITHM": "hashlib.sha512",
    "AUTH_TOKEN_CHARACTER_LENGTH": 64,
    "TOKEN_TTL": timedelta(days=7),  # Token expires after 7 days
    "USER_SERIALIZER": "gardeniq.users.serializers.UserDetailReadOnlySerializer",
    "TOKEN_LIMIT_PER_USER": 5,  # Limit to 5 tokens per user
    "AUTO_REFRESH": False,
    "MIN_REFRESH_INTERVAL": 60,  # Minimum interval (in seconds) before a token can be refreshed
    "EXPIRY_DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S.%fZ",
}
