from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Add any additional fields you need here.
    """
    # Example of an additional field
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name='Номер телефона') # Corrected verbose_name and removed duplicate
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар') # Added avatar field
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name='Страна') # Added country field

    # Set email as the username field for authentication
    USERNAME_FIELD = 'email'
    # username and other fields are required by default, but email is now the USERNAME_FIELD
    REQUIRED_FIELDS = ['username'] # Include username here if you want it required

    # Add related_name to groups and user_permissions to avoid clashes
    # if you are using these in other apps
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions '
                  'granted to each of their groups.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
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
