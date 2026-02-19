from django.db import models


class Table(models.Model):
    class Status(models.TextChoices):
        FREE     = "FREE",     "Bo'sh"
        OCCUPIED = "OCCUPIED", "Band"

    number     = models.PositiveIntegerField(unique=True, verbose_name="Stol raqami")
    status     = models.CharField(
        max_length=10, choices=Status.choices,
        default=Status.FREE, verbose_name="Holati"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan")

    class Meta:
        ordering            = ["number"]
        verbose_name        = "Stol"
        verbose_name_plural = "Stollar"

    def __str__(self) -> str:
        return f"Stol {self.number} [{self.get_status_display()}]"
