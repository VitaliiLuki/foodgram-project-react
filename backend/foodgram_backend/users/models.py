from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Create and saves a user's data"""
    USER = 'user'
    ADMIN = 'admin'

    USER_ROLES = (
        (USER, 'user'),
        (ADMIN, 'admin')
    )

    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=150,
        unique=True
    )
    first_name = models.CharField(
        max_length=150,
    )
    last_name = models.CharField(
        max_length=150,
    )
    password = models.CharField(
        max_length=150,
    )
    new_password = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        default=None
    )
    role = models.CharField(
        max_length=20,
        choices=USER_ROLES,
        blank=True,
        default=USER,
    )

    USERNAME_FIELD = 'username'

    @property
    def is_user(self):
        return self.role == User.USER

    @property
    def is_admin(self):
        return (self.role == User.ADMIN or self.is_superuser
                or self.is_staff)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['id']
