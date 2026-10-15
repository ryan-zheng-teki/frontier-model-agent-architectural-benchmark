"""Comprehensive unit tests for OrderService and InternalBillingService."""

import unittest
from unittest.mock import MagicMock

from order_service import OrderService
from internal_billing_service import InternalBillingService, PaymentFailedError


class Customer:
    def __init__(self, customer_id: str, is_active: bool, payment_token: str, email: str):
        self.customer_id = customer_id
        self.is_active = is_active
        self.payment_token = payment_token
        self.email = email


class Order:
    def __init__(self, order_id: str, status: str):
        self.order_id = order_id
        self.status = status


class PaymentResult:
    def __init__(self, success: bool, error: str = ""):
        self.success = success
        self.error = error


class TestOrderService(unittest.TestCase):
    """Verifies that OrderService retains 100% of its domain invariants and behavior."""

    def setUp(self):
        self.db = MagicMock()
        self.gateway = MagicMock()
        self.notification = MagicMock()
        self.service = OrderService(self.db, self.gateway, self.notification)

    def test_process_order_success(self):
        customer = Customer("cust_1", is_active=True, payment_token="tok_123", email="user@example.com")
        order = Order("ord_1", status="PENDING")
        self.db.get_customer.return_value = customer
        self.db.get_order.return_value = order
        self.gateway.charge.return_value = PaymentResult(success=True)

        result = self.service.process_order("ord_1", "cust_1", 99.99)

        self.assertEqual(result.status, "PAID")
        self.gateway.charge.assert_called_once_with("tok_123", 99.99)
        self.db.save_order.assert_called_once_with(order)
        self.notification.send_receipt.assert_called_once_with("user@example.com", order)

    def test_process_order_rejects_non_positive_amount(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.process_order("ord_1", "cust_1", 0)
        self.assertIn("Amount must be positive", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.service.process_order("ord_1", "cust_1", -10.0)
        self.assertIn("Amount must be positive", str(ctx.exception))

    def test_process_order_rejects_missing_customer(self):
        self.db.get_customer.return_value = None
        with self.assertRaises(ValueError) as ctx:
            self.service.process_order("ord_1", "cust_missing", 50.0)
        self.assertIn("Invalid or inactive customer", str(ctx.exception))

    def test_process_order_rejects_inactive_customer(self):
        customer = Customer("cust_1", is_active=False, payment_token="tok_123", email="user@example.com")
        self.db.get_customer.return_value = customer
        with self.assertRaises(ValueError) as ctx:
            self.service.process_order("ord_1", "cust_1", 50.0)
        self.assertIn("Invalid or inactive customer", str(ctx.exception))

    def test_process_order_rejects_missing_order(self):
        customer = Customer("cust_1", is_active=True, payment_token="tok_123", email="user@example.com")
        self.db.get_customer.return_value = customer
        self.db.get_order.return_value = None

        with self.assertRaises(ValueError) as ctx:
            self.service.process_order("ord_missing", "cust_1", 50.0)
        self.assertIn("Order is not in pending state", str(ctx.exception))

    def test_process_order_rejects_non_pending_order(self):
        customer = Customer("cust_1", is_active=True, payment_token="tok_123", email="user@example.com")
        order = Order("ord_1", status="PAID")
        self.db.get_customer.return_value = customer
        self.db.get_order.return_value = order

        with self.assertRaises(ValueError) as ctx:
            self.service.process_order("ord_1", "cust_1", 50.0)
        self.assertIn("Order is not in pending state", str(ctx.exception))

    def test_process_order_handles_payment_failure(self):
        customer = Customer("cust_1", is_active=True, payment_token="tok_123", email="user@example.com")
        order = Order("ord_1", status="PENDING")
        self.db.get_customer.return_value = customer
        self.db.get_order.return_value = order
        self.gateway.charge.return_value = PaymentResult(success=False, error="Card expired")

        with self.assertRaises(Exception) as ctx:
            self.service.process_order("ord_1", "cust_1", 50.0)
        self.assertIn("Payment failed: Card expired", str(ctx.exception))
        self.db.save_order.assert_not_called()
        self.notification.send_receipt.assert_not_called()


class TestInternalBillingService(unittest.TestCase):
    """Verifies that InternalBillingService satisfies enterprise billing requirements in isolation."""

    def setUp(self):
        self.db = MagicMock()
        self.gateway = MagicMock()
        self.service = InternalBillingService(self.db, self.gateway)

    def test_dependencies_are_strictly_isolated(self):
        # Must only require db and gateway; does NOT take notification_service
        self.assertTrue(hasattr(self.service, "db"))
        self.assertTrue(hasattr(self.service, "payment_gateway"))
        self.assertFalse(hasattr(self.service, "notification_service"))

    def test_charge_enterprise_account_success(self):
        # Corporate enterprise account: pre-verified upstream.
        # Even if is_active is False or absent, customer status check is intentionally not enforced.
        enterprise_account = Customer("corp_ent_1", is_active=False, payment_token="corp_tok_999", email="billing@corp.com")
        self.db.get_customer.return_value = enterprise_account
        self.gateway.charge.return_value = PaymentResult(success=True)

        result = self.service.charge_enterprise_account(
            account_id="corp_ent_1",
            amount=5000.0,
            reference="sub-job-2026-10",
            requested_by="SubscriptionBatchRunner",
        )

        self.assertTrue(result.success)
        self.gateway.charge.assert_called_once_with("corp_tok_999", 5000.0)
        # Verify complete isolation from order and notification systems
        self.assertFalse(hasattr(self.db, "get_order") and self.db.get_order.called)
        self.assertFalse(hasattr(self.db, "save_order") and self.db.save_order.called)

    def test_process_payment_alias_works(self):
        enterprise_account = Customer("corp_ent_2", is_active=True, payment_token="corp_tok_888", email="admin@corp.com")
        self.db.get_customer.return_value = enterprise_account
        self.gateway.charge.return_value = PaymentResult(success=True)

        result = self.service.process_payment(
            account_id="corp_ent_2",
            amount=1250.50,
            reference="batch-job-42",
        )

        self.assertTrue(result.success)
        self.gateway.charge.assert_called_once_with("corp_tok_888", 1250.50)

    def test_charge_rejects_missing_account_id(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.charge_enterprise_account("", 100.0)
        self.assertIn("account_id is required", str(ctx.exception))

    def test_charge_rejects_non_positive_amount(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.charge_enterprise_account("corp_1", 0)
        self.assertIn("Amount must be positive", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.service.charge_enterprise_account("corp_1", -150.0)
        self.assertIn("Amount must be positive", str(ctx.exception))

    def test_charge_rejects_nan_or_infinite_amount(self):
        with self.assertRaises(ValueError):
            self.service.charge_enterprise_account("corp_1", float("nan"))
        with self.assertRaises(ValueError):
            self.service.charge_enterprise_account("corp_1", float("inf"))

    def test_charge_rejects_unknown_account_or_missing_token(self):
        self.db.get_customer.return_value = None
        with self.assertRaises(ValueError) as ctx:
            self.service.charge_enterprise_account("corp_unknown", 250.0)
        self.assertIn("missing payment token", str(ctx.exception))

        account_no_token = Customer("corp_no_token", is_active=True, payment_token="", email="test@corp.com")
        self.db.get_customer.return_value = account_no_token
        with self.assertRaises(ValueError) as ctx:
            self.service.charge_enterprise_account("corp_no_token", 250.0)
        self.assertIn("missing payment token", str(ctx.exception))

    def test_charge_raises_payment_failed_error_on_gateway_decline(self):
        enterprise_account = Customer("corp_ent_1", is_active=True, payment_token="tok_fail", email="billing@corp.com")
        self.db.get_customer.return_value = enterprise_account
        self.gateway.charge.return_value = PaymentResult(success=False, error="Insufficient corporate credit limit")

        with self.assertRaises(PaymentFailedError) as ctx:
            self.service.charge_enterprise_account("corp_ent_1", 10000.0)
        self.assertIn("Insufficient corporate credit limit", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
