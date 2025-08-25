from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Add any additional fields you need here.
    """
    # Example of an additional field
    phone_number = models.CharField(
        max_length=15, blank=True, null=True, verbose_name='Номер телефона'
    )  # Corrected verbose_name and removed duplicate
    avatar = models.ImageField(
        upload_to='avatars/', blank=True, null=True, verbose_name='Аватар'
    )  # Added avatar field
    country = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='Страна'
    )  # Added country field

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.'
                  'A user will get all permissions '
                  'granted to each of their groups.',
        related_name="custom_user_set",
        related_query_name="custom_user", )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )

    def __str__(self):
        return self.username
