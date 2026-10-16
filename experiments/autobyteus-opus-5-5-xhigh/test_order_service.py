import inspect
import unittest
from types import SimpleNamespace
from unittest import mock

from order_service import OrderService


def make_customer(is_active=True):
    return SimpleNamespace(
        is_active=is_active, payment_token="tok_123", email="buyer@example.com"
    )


def make_order(status="PENDING"):
    return SimpleNamespace(id="order_1", status=status)


class OrderServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.db = mock.Mock()
        self.gateway = mock.Mock()
        self.notifications = mock.Mock()
        self.service = OrderService(self.db, self.gateway, self.notifications)
        self.customer = make_customer()
        self.order = make_order()
        self.db.get_customer.return_value = self.customer
        self.db.get_order.return_value = self.order
        self.gateway.charge.return_value = SimpleNamespace(success=True, error=None)

    def fail_charge(self, error="card declined"):
        self.gateway.charge.return_value = SimpleNamespace(success=False, error=error)

    def assert_nothing_charged_or_saved(self):
        self.gateway.charge.assert_not_called()
        self.db.save_order.assert_not_called()


class ProcessOrderTests(OrderServiceTestCase):
    """Customer checkout path: behavior is preserved exactly (REQ-001)."""

    # AC-001
    def test_success_charges_marks_paid_saves_and_sends_receipt(self):
        result = self.service.process_order("order_1", "cust_1", 25.0)

        self.assertIs(result, self.order)
        self.db.get_customer.assert_called_once_with("cust_1")
        self.db.get_order.assert_called_once_with("order_1")
        self.gateway.charge.assert_called_once_with("tok_123", 25.0)
        self.assertEqual(self.order.status, "PAID")
        self.db.save_order.assert_called_once_with(self.order)
        self.notifications.send_receipt.assert_called_once_with(
            "buyer@example.com", self.order
        )

    # AC-002
    def test_non_positive_amount_is_rejected(self):
        for amount in (0, -5.0):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError) as ctx:
                    self.service.process_order("order_1", "cust_1", amount)
                self.assertEqual(str(ctx.exception), "Amount must be positive")
        self.db.get_customer.assert_not_called()
        self.assert_nothing_charged_or_saved()
        self.notifications.send_receipt.assert_not_called()

    def test_missing_customer_is_rejected(self):
        self.db.get_customer.return_value = None
        with self.assertRaises(ValueError) as ctx:
            self.service.process_order("order_1", "cust_1", 25.0)
        self.assertEqual(str(ctx.exception), "Invalid or inactive customer")
        self.db.get_order.assert_not_called()
        self.assert_nothing_charged_or_saved()
        self.notifications.send_receipt.assert_not_called()

    def test_inactive_customer_is_rejected(self):
        self.customer.is_active = False
        with self.assertRaises(ValueError) as ctx:
            self.service.process_order("order_1", "cust_1", 25.0)
        self.assertEqual(str(ctx.exception), "Invalid or inactive customer")
        self.db.get_order.assert_not_called()
        self.assert_nothing_charged_or_saved()
        self.notifications.send_receipt.assert_not_called()

    def test_missing_order_is_rejected(self):
        self.db.get_order.return_value = None
        with self.assertRaises(ValueError) as ctx:
            self.service.process_order("order_1", "cust_1", 25.0)
        self.assertEqual(str(ctx.exception), "Order is not in pending state")
        self.assert_nothing_charged_or_saved()
        self.notifications.send_receipt.assert_not_called()

    def test_non_pending_order_is_rejected(self):
        for status in ("PAID", "ACTIVE"):
            with self.subTest(status=status):
                self.order.status = status
                with self.assertRaises(ValueError) as ctx:
                    self.service.process_order("order_1", "cust_1", 25.0)
                self.assertEqual(str(ctx.exception), "Order is not in pending state")
                self.assertEqual(self.order.status, status)
        self.assert_nothing_charged_or_saved()
        self.notifications.send_receipt.assert_not_called()

    def test_payment_failure_raises_and_leaves_order_unchanged(self):
        self.fail_charge("card declined")
        with self.assertRaises(Exception) as ctx:
            self.service.process_order("order_1", "cust_1", 25.0)
        self.assertIs(type(ctx.exception), Exception)
        self.assertEqual(str(ctx.exception), "Payment failed: card declined")
        self.assertEqual(self.order.status, "PENDING")
        self.db.save_order.assert_not_called()
        self.notifications.send_receipt.assert_not_called()

    # AC-008
    def test_signature_has_no_parameter_that_relaxes_checks(self):
        params = list(inspect.signature(OrderService.process_order).parameters)
        self.assertEqual(params, ["self", "order_id", "customer_id", "amount"])


class ProcessInternalEnterprisePaymentTests(OrderServiceTestCase):
    """Internal enterprise charge: relaxed checks, no notification (REQ-002 to REQ-004)."""

    def pay(self, amount=25.0):
        return self.service.process_internal_enterprise_payment("order_1", "cust_1", amount)

    # AC-003, AC-004
    def test_charges_inactive_customer_for_non_pending_order(self):
        self.customer.is_active = False
        for status in ("PAID", "ACTIVE"):
            with self.subTest(status=status):
                self.gateway.charge.reset_mock()
                self.db.save_order.reset_mock()
                self.order.status = status

                result = self.pay(40.0)

                self.assertIs(result, self.order)
                self.gateway.charge.assert_called_once_with("tok_123", 40.0)
                self.assertEqual(self.order.status, "PAID")
                self.db.save_order.assert_called_once_with(self.order)
        self.assertEqual(self.notifications.mock_calls, [])

    # AC-003, AC-004
    def test_success_for_active_customer_and_pending_order_sends_nothing(self):
        result = self.pay()

        self.assertIs(result, self.order)
        self.db.get_customer.assert_called_once_with("cust_1")
        self.db.get_order.assert_called_once_with("order_1")
        self.gateway.charge.assert_called_once_with("tok_123", 25.0)
        self.assertEqual(self.order.status, "PAID")
        self.db.save_order.assert_called_once_with(self.order)
        self.assertEqual(self.notifications.mock_calls, [])

    # AC-005
    def test_non_positive_amount_is_rejected(self):
        for amount in (0, -5.0):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError) as ctx:
                    self.pay(amount)
                self.assertEqual(str(ctx.exception), "Amount must be positive")
        self.assert_nothing_charged_or_saved()
        self.assertEqual(self.notifications.mock_calls, [])

    # AC-006
    def test_missing_customer_is_rejected(self):
        self.db.get_customer.return_value = None
        with self.assertRaises(ValueError) as ctx:
            self.pay()
        self.assertEqual(str(ctx.exception), "Customer not found")
        self.assert_nothing_charged_or_saved()
        self.assertEqual(self.notifications.mock_calls, [])

    # AC-006
    def test_missing_order_is_rejected(self):
        self.db.get_order.return_value = None
        with self.assertRaises(ValueError) as ctx:
            self.pay()
        self.assertEqual(str(ctx.exception), "Order not found")
        self.assert_nothing_charged_or_saved()
        self.assertEqual(self.notifications.mock_calls, [])

    # AC-007, AC-004
    def test_payment_failure_raises_and_leaves_order_unchanged(self):
        self.order.status = "ACTIVE"
        self.fail_charge("insufficient funds")
        with self.assertRaises(Exception) as ctx:
            self.pay()
        self.assertIs(type(ctx.exception), Exception)
        self.assertEqual(str(ctx.exception), "Payment failed: insufficient funds")
        self.assertEqual(self.order.status, "ACTIVE")
        self.db.save_order.assert_not_called()
        self.assertEqual(self.notifications.mock_calls, [])

    # AC-008
    def test_signature_matches_process_order_identity_shape(self):
        params = list(
            inspect.signature(OrderService.process_internal_enterprise_payment).parameters
        )
        self.assertEqual(params, ["self", "order_id", "customer_id", "amount"])


if __name__ == "__main__":
    unittest.main()
