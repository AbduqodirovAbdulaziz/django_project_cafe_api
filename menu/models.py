from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name       = models.CharField(max_length=80, unique=True, verbose_name="Nomi")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Tartib raqami")
    is_active  = models.BooleanField(default=True, verbose_name="Faolmi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan")

    class Meta:
        ordering         = ["sort_order", "name"]
        verbose_name     = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self) -> str:
        return self.name


class MenuItem(models.Model):
    category  = models.ForeignKey(
        Category, on_delete=models.PROTECT,
        related_name="items", verbose_name="Kategoriya"
    )
    name      = models.CharField(max_length=120, verbose_name="Nomi")
    price     = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Narxi",
    )
    description      = models.TextField(blank=True, verbose_name="Tavsif")
    image            = models.ImageField(upload_to="menu/", blank=True, null=True, verbose_name="Rasm")
    is_available     = models.BooleanField(default=True, verbose_name="Mavjudmi")
    prep_time_minutes = models.PositiveIntegerField(default=0, verbose_name="Tayyorlash vaqti (daq)")
    created_at       = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan")
    updated_at       = models.DateTimeField(auto_now=True, verbose_name="Yangilangan")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"],
                name="uniq_menuitem_name_per_category"
            ),
        ]
        ordering            = ["category__sort_order", "category__name", "name"]
        verbose_name        = "Menyu elementi"
        verbose_name_plural = "Menyu elementlari"

    def __str__(self) -> str:
        return f"{self.name} ({self.category.name})"
