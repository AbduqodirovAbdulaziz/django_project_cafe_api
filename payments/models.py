from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from orders.models import Order


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "CASH", "Naqd pul"
        CARD = "CARD", "Karta"
        QR   = "QR",   "QR kod"

    order       = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name="payments", verbose_name="Buyurtma"
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="payments_received", verbose_name="Qabul qiluvchi"
    )
    method      = models.CharField(
        max_length=10, choices=Method.choices, verbose_name="To'lov usuli"
    )
    amount      = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Miqdori"
    )
    is_debt     = models.BooleanField(default=False, verbose_name="Qarzmi")
    debt_note   = models.CharField(max_length=255, blank=True, verbose_name="Qarz izohi")
    paid_at     = models.DateTimeField(auto_now_add=True, verbose_name="To'langan vaqt")

    class Meta:
        ordering            = ["-paid_at"]
        verbose_name        = "To'lov"
        verbose_name_plural = "To'lovlar"

    def __str__(self) -> str:
        return f"{self.get_method_display()} — {self.amount} (Buyurtma #{self.order_id})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.order.recalculate_totals()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.recalculate_totals()
