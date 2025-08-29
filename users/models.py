from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Кастомный менеджер для модели User с email вместо username."""

    def create_user(self, email, password=None, **extra_fields):
        """Создает и возвращает пользователя с email и паролем."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создает и возвращает суперпользователя."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = models.CharField(max_length=150, blank=True, null=True, verbose_name='Имя пользователя')
    email = models.EmailField(unique=True, verbose_name='Email')
    avatar = models.ImageField(upload_to='users/', blank=True, null=True, verbose_name='Аватар')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Номер телефона')
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name='Страна')
    email_verified = models.BooleanField(default=False, verbose_name='Email подтвержден')
    verification_token = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

