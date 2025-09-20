from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model that uses email as the primary identifier.
    """
    username = None  # Remove username field
    email = models.EmailField(unique=True, verbose_name="Email Address")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is already required, no additional required fields
    
    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
