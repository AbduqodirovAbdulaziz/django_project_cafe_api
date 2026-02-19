from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from tables.models import Table
from menu.models import Category, MenuItem
from .models import Order, OrderItem, OrderStatusLog
from payments.models import Payment
from decimal import Decimal


class OrderModelTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="manager", password="pass", role=User.Role.MANAGER)
		self.table = Table.objects.create(number=1)
		self.cat = Category.objects.create(name="Drinks")
		self.item1 = MenuItem.objects.create(category=self.cat, name="Tea", price=Decimal("1.50"))
		self.item2 = MenuItem.objects.create(category=self.cat, name="Coffee", price=Decimal("2.00"))

	def test_create_order_with_items_and_totals(self):
		order = Order.objects.create(order_type=Order.OrderType.DINE_IN, table=self.table, created_by=self.user)
		oi1 = OrderItem.objects.create(order=order, menu_item=self.item1, qty=2)
		oi2 = OrderItem.objects.create(order=order, menu_item=self.item2, qty=1)

		order.recalculate_totals()
		self.assertEqual(order.subtotal, oi1.line_total + oi2.line_total)
		self.assertEqual(order.total, order.subtotal)
		self.assertEqual(order.due_amount, order.total)

	def test_status_transitions_and_logs(self):
		order = Order.objects.create(order_type=Order.OrderType.DINE_IN, table=self.table, created_by=self.user)
		# NEW -> COOKING
		order.change_status(to_status=Order.Status.COOKING, by_user=self.user, comment="start")
		order.refresh_from_db()
		self.assertEqual(order.status, Order.Status.COOKING)
		self.assertTrue(OrderStatusLog.objects.filter(order=order, to_status=Order.Status.COOKING).exists())

		# COOKING -> READY
		order.change_status(to_status=Order.Status.READY, by_user=self.user)
		order.refresh_from_db()
		self.assertEqual(order.status, Order.Status.READY)

		# READY -> SERVED -> PAID
		order.change_status(to_status=Order.Status.SERVED, by_user=self.user)
		order.change_status(to_status=Order.Status.PAID, by_user=self.user)
		order.refresh_from_db()
		self.assertEqual(order.status, Order.Status.PAID)

	def test_payments_update_totals_and_due(self):
		order = Order.objects.create(order_type=Order.OrderType.DINE_IN, table=self.table, created_by=self.user)
		OrderItem.objects.create(order=order, menu_item=self.item1, qty=3)
		order.recalculate_totals()

		self.assertEqual(order.paid_total, 0)
		Payment.objects.create(order=order, received_by=self.user, method=Payment.Method.CASH, amount=order.total)
		order.refresh_from_db()
		self.assertEqual(order.paid_total, order.total)
		self.assertEqual(order.due_amount, 0)
