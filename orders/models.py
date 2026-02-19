from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Sum
from decimal import Decimal
import uuid

from tables.models import Table
from menu.models import MenuItem


class Order(models.Model):
    class OrderType(models.TextChoices):
        DINE_IN = "DINE_IN", "Dine in"
        TAKEAWAY = "TAKEAWAY", "Takeaway"

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        COOKING = "COOKING", "Cooking"
        READY = "READY", "Ready"
        SERVED = "SERVED", "Served"
        PAID = "PAID", "Paid"
        CANCELED = "CANCELED", "Canceled"

    class DiscountType(models.TextChoices):
        NONE = "NONE", "None"
        PERCENT = "PERCENT", "Percent"
        AMOUNT = "AMOUNT", "Amount"

    order_code = models.CharField(max_length=12, unique=True, blank=True, editable=False)

    order_type = models.CharField(max_length=10, choices=OrderType.choices)
    table = models.ForeignKey(Table, on_delete=models.PROTECT, null=True, blank=True, related_name="orders")

    customer_name = models.CharField(max_length=120, blank=True)
    customer_phone = models.CharField(max_length=30, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders_created")

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)
    notes = models.TextField(blank=True)

    # totals (stored for reports)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_type = models.CharField(max_length=10, choices=DiscountType.choices, default=DiscountType.NONE)
    discount_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    paid_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    is_closed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ["-created_at"]
        verbose_name        = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"

    def __str__(self) -> str:
        return f"Buyurtma #{self.id} ({self.get_status_display()})"

    def clean(self):
        # Conditional requirements
        if self.order_type == self.OrderType.DINE_IN and not self.table_id:
            raise ValidationError({"table": "DINE_IN buyurtmada table majburiy."})

        if self.order_type == self.OrderType.TAKEAWAY and not self.customer_name.strip():
            raise ValidationError({"customer_name": "TAKEAWAY buyurtmada customer_name majburiy."})

        # discount sanity
        if self.discount_type == self.DiscountType.PERCENT:
            if self.discount_value < 0 or self.discount_value > 100:
                raise ValidationError({"discount_value": "PERCENT 0..100 oralig'ida bo'lishi kerak."})
        if self.discount_type == self.DiscountType.AMOUNT:
            if self.discount_value < 0:
                raise ValidationError({"discount_value": "AMOUNT manfiy bo'lmaydi."})

    def save(self, *args, **kwargs):
        # generate code once
        if not self.order_code:
            self.order_code = uuid.uuid4().hex[:12].upper()

        old_status = None
        old_table_id = None
        if self.pk:
            old = Order.objects.filter(pk=self.pk).values("status", "table_id").first()
            if old:
                old_status = old["status"]
                old_table_id = old["table_id"]

        super().save(*args, **kwargs)

        # sync table occupancy (simple + deterministic)
        self._sync_table_status(old_status=old_status, old_table_id=old_table_id)

    def _sync_table_status(self, old_status=None, old_table_id=None):
        # if table changed, free old one
        if old_table_id and old_table_id != self.table_id:
            Table.objects.filter(id=old_table_id).update(status=Table.Status.FREE)

        # update current table based on order state
        if not self.table_id:
            return

        if self.status in (self.Status.PAID, self.Status.CANCELED):
            Table.objects.filter(id=self.table_id).update(status=Table.Status.FREE)
        else:
            Table.objects.filter(id=self.table_id).update(status=Table.Status.OCCUPIED)

    def delete(self, *args, **kwargs):
        """Free the table before deleting the order."""
        if self.table_id:
            Table.objects.filter(id=self.table_id).update(status=Table.Status.FREE)
        super().delete(*args, **kwargs)

    def recalculate_totals(self):
        """
        Recompute subtotal/discount/total + payments (paid_total/due_amount).
        Safe update: uses queryset.update to avoid recursion.
        """
        if not self.pk:
            return

        subtotal = (
            self.items.aggregate(s=Sum("line_total")).get("s") or Decimal("0.00")
        )

        # discount
        discount_amount = Decimal("0.00")
        if self.discount_type == self.DiscountType.PERCENT:
            discount_amount = (subtotal * (self.discount_value / Decimal("100.00"))).quantize(Decimal("0.01"))
        elif self.discount_type == self.DiscountType.AMOUNT:
            discount_amount = self.discount_value

        if discount_amount < 0:
            discount_amount = Decimal("0.00")
        if discount_amount > subtotal:
            discount_amount = subtotal

        total = (subtotal - discount_amount).quantize(Decimal("0.01"))
        if total < 0:
            total = Decimal("0.00")

        paid_total = (
            self.payments.filter(is_debt=False).aggregate(s=Sum("amount")).get("s") or Decimal("0.00")
        )
        due_amount = (total - paid_total).quantize(Decimal("0.01"))
        if due_amount < 0:
            due_amount = Decimal("0.00")

        is_closed = self.status in (self.Status.PAID, self.Status.CANCELED)

        Order.objects.filter(pk=self.pk).update(
            subtotal=subtotal,
            discount_amount=discount_amount,
            total=total,
            paid_total=paid_total,
            due_amount=due_amount,
            is_closed=is_closed,
        )

        # keep instance in sync (optional but useful)
        self.subtotal = subtotal
        self.discount_amount = discount_amount
        self.total = total
        self.paid_total = paid_total
        self.due_amount = due_amount
        self.is_closed = is_closed

    @transaction.atomic
    def change_status(self, to_status: str, by_user, comment: str = ""):
        """
        Status transition + log (API shu methodni ishlatadi).
        """
        from_status = self.status
        if from_status == to_status:
            return

        # Minimal transition rules (qattiq)
        allowed = {
            self.Status.NEW: {self.Status.COOKING, self.Status.CANCELED},
            self.Status.COOKING: {self.Status.READY, self.Status.CANCELED},
            self.Status.READY: {self.Status.SERVED, self.Status.CANCELED},
            self.Status.SERVED: {self.Status.PAID, self.Status.CANCELED},
            self.Status.PAID: set(),
            self.Status.CANCELED: set(),
        }
        if to_status not in allowed.get(from_status, set()):
            raise ValidationError(f"Status transition mumkin emas: {from_status} -> {to_status}")

        self.status = to_status
        self.save(update_fields=["status", "updated_at"])

        OrderStatusLog.objects.create(
            order=self,
            from_status=from_status,
            to_status=to_status,
            changed_by=by_user,
            comment=comment or "",
        )

        # paid/canceled bo'lsa stolni bo'shatadi (save ichida sync bor)
        self.recalculate_totals()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name="order_items")

    # snapshot (menu o'zgarsa ham order buzilmaydi)
    item_name_snapshot = models.CharField(max_length=120, blank=True)
    unit_price_snapshot = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    qty = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    notes = models.CharField(max_length=255, blank=True)

    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ["id"]
        verbose_name        = "Buyurtma elementi"
        verbose_name_plural = "Buyurtma elementlari"

    def __str__(self) -> str:
        return f"{self.qty} × {self.item_name_snapshot or self.menu_item.name}"

    def save(self, *args, **kwargs):
        if not self.item_name_snapshot:
            self.item_name_snapshot = self.menu_item.name
        if self.unit_price_snapshot == Decimal("0.00"):
            self.unit_price_snapshot = self.menu_item.price

        self.line_total = (Decimal(self.qty) * self.unit_price_snapshot).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)

        # after item update, recompute order totals
        self.order.recalculate_totals()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.recalculate_totals()


class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.CharField(max_length=10)
    to_status = models.CharField(max_length=10)

    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="status_changes")
    changed_at = models.DateTimeField(auto_now_add=True)
    comment = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering            = ["-changed_at"]
        verbose_name        = "Status o'zgarishi"
        verbose_name_plural = "Status o'zgarishlari"

    def __str__(self) -> str:
        return f"Buyurtma #{self.order_id}: {self.from_status} → {self.to_status}"
