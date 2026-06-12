from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, blank=True)

    def __str__(self):
        return self.get_full_name() or self.username
