from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        MANAGER = "MANAGER", "Menejer"
        WAITER  = "WAITER",  "Ofitsiant"
        CHEF    = "CHEF",    "Oshpaz"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.WAITER,
        verbose_name="Rol",
    )

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"
