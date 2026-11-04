from django.contrib.auth.models import AbstractUser
from django.db import models

class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Администратор'
    ENGINEER = 'ENGINEER', 'Инженер/Оператор'

class User(AbstractUser):
    role = models.CharField(
        max_length=20, 
        choices=UserRole.choices, 
        default=UserRole.ENGINEER,
        verbose_name="Роль в системе"
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN or self.is_superuser