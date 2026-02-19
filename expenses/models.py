from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class ExpenseCategory(models.Model):
    name       = models.CharField(max_length=80, unique=True, verbose_name="Nomi")
    is_active  = models.BooleanField(default=True, verbose_name="Faolmi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan")

    class Meta:
        verbose_name        = "Xarajat kategoriyasi"
        verbose_name_plural = "Xarajat kategoriyalari"

    def __str__(self) -> str:
        return self.name


class Expense(models.Model):
    category   = models.ForeignKey(
        ExpenseCategory, on_delete=models.PROTECT,
        related_name="expenses", verbose_name="Kategoriya"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="expenses_created", verbose_name="Kim tomonidan"
    )
    amount     = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Miqdori"
    )
    comment    = models.CharField(max_length=255, blank=True, verbose_name="Izoh")
    spent_at   = models.DateTimeField(verbose_name="Xarajat sanasi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan")

    class Meta:
        ordering            = ["-spent_at"]
        verbose_name        = "Xarajat"
        verbose_name_plural = "Xarajatlar"

    def __str__(self) -> str:
        return f"{self.category.name}: {self.amount}"
