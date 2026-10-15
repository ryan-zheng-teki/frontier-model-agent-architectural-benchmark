import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call

from order_service import OrderService


class ForbiddenDependency:
    """Fail on any access, including reads that a mock might not record."""

    def __getattribute__(self, name):
        raise AssertionError(f"Payment-only flow accessed forbidden dependency: {name}")


class PaymentTests(unittest.TestCase):
    def setUp(self):
        self.gateway = Mock(spec=["charge"])
        self.service = OrderService(
            ForbiddenDependency(), self.gateway, ForbiddenDependency()
        )

    def test_success_returns_exact_gateway_result_without_lifecycle_access(self):
        result = SimpleNamespace(success=True)
        self.gateway.charge.return_value = result

        returned = self.service.process_payment("enterprise-token", 125.5)

        self.assertIs(returned, result)
        self.gateway.charge.assert_called_once_with("enterprise-token", 125.5)

    def test_nonpositive_amounts_fail_before_charge_without_lifecycle_access(self):
        for amount in (0, -1, -0.01):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError) as raised:
                    self.service.process_payment("enterprise-token", amount)
                self.assertEqual(str(raised.exception), "Amount must be positive")
                self.gateway.charge.assert_not_called()

    def test_rejection_preserves_error_without_lifecycle_access(self):
        self.gateway.charge.return_value = SimpleNamespace(
            success=False, error="Card declined"
        )

        with self.assertRaises(Exception) as raised:
            self.service.process_payment("enterprise-token", 125.5)

        self.assertIs(type(raised.exception), Exception)
        self.assertEqual(str(raised.exception), "Payment failed: Card declined")
        self.gateway.charge.assert_called_once_with("enterprise-token", 125.5)

    def test_gateway_exception_propagates_unchanged_without_lifecycle_access(self):
        failure = RuntimeError("Gateway unavailable")
        self.gateway.charge.side_effect = failure

        with self.assertRaises(RuntimeError) as raised:
            self.service.process_payment("enterprise-token", 125.5)

        self.assertIs(raised.exception, failure)
        self.gateway.charge.assert_called_once_with("enterprise-token", 125.5)


class CheckoutTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock(spec=["get_customer", "get_order", "save_order"])
        self.gateway = Mock(spec=["charge"])
        self.notifier = Mock(spec=["send_receipt"])
        self.calls = Mock()
        self.calls.attach_mock(self.db, "db")
        self.calls.attach_mock(self.gateway, "gateway")
        self.calls.attach_mock(self.notifier, "notifier")
        self.customer = SimpleNamespace(
            is_active=True, payment_token="customer-token", email="customer@example.com"
        )
        self.order = SimpleNamespace(status="PENDING")
        self.db.get_customer.return_value = self.customer
        self.db.get_order.return_value = self.order
        self.gateway.charge.return_value = SimpleNamespace(success=True)
        self.service = OrderService(self.db, self.gateway, self.notifier)

    def test_success_preserves_charge_paid_save_receipt_and_same_order(self):
        def charge(token, amount):
            self.assertEqual(self.order.status, "PENDING")
            return SimpleNamespace(success=True)

        def save(order):
            self.assertIs(order, self.order)
            self.assertEqual(order.status, "PAID")

        def receipt(email, order):
            self.assertEqual(order.status, "PAID")
            self.db.save_order.assert_called_once_with(order)

        self.gateway.charge.side_effect = charge
        self.db.save_order.side_effect = save
        self.notifier.send_receipt.side_effect = receipt

        returned = self.service.process_order("order-id", "customer-id", 49.5)

        self.assertIs(returned, self.order)
        self.assertEqual(self.order.status, "PAID")
        self.assertEqual(self.calls.mock_calls, [
            call.db.get_customer("customer-id"),
            call.db.get_order("order-id"),
            call.gateway.charge("customer-token", 49.5),
            call.db.save_order(self.order),
            call.notifier.send_receipt("customer@example.com", self.order),
        ])

    def test_nonpositive_amounts_fail_before_any_dependency_access(self):
        service = OrderService(
            ForbiddenDependency(), ForbiddenDependency(), ForbiddenDependency()
        )
        for amount in (0, -1, -0.01):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError) as raised:
                    service.process_order("order-id", "customer-id", amount)
                self.assertEqual(str(raised.exception), "Amount must be positive")

    def test_missing_or_inactive_customer_fails_before_order_lookup(self):
        for customer in (None, SimpleNamespace(is_active=False)):
            with self.subTest(customer=customer):
                self.calls.reset_mock()
                self.db.get_customer.return_value = customer
                with self.assertRaises(ValueError) as raised:
                    self.service.process_order("order-id", "customer-id", 49.5)
                self.assertEqual(str(raised.exception), "Invalid or inactive customer")
                self.assertEqual(self.calls.mock_calls, [
                    call.db.get_customer("customer-id")
                ])
                self.assertEqual(self.order.status, "PENDING")

    def test_missing_or_nonpending_order_fails_before_charge(self):
        for order in (None, SimpleNamespace(status="PAID"),
                      SimpleNamespace(status="CANCELLED")):
            with self.subTest(order=order):
                self.calls.reset_mock()
                self.db.get_order.return_value = order
                with self.assertRaises(ValueError) as raised:
                    self.service.process_order("order-id", "customer-id", 49.5)
                self.assertEqual(str(raised.exception), "Order is not in pending state")
                self.assertEqual(self.calls.mock_calls, [
                    call.db.get_customer("customer-id"),
                    call.db.get_order("order-id"),
                ])
                if order is not None:
                    self.assertIn(order.status, ("PAID", "CANCELLED"))

    def test_rejection_prevents_order_completion(self):
        self.gateway.charge.return_value = SimpleNamespace(
            success=False, error="Card declined"
        )

        with self.assertRaises(Exception) as raised:
            self.service.process_order("order-id", "customer-id", 49.5)

        self.assertIs(type(raised.exception), Exception)
        self.assertEqual(str(raised.exception), "Payment failed: Card declined")
        self.assert_failed_payment_calls()

    def test_gateway_exception_propagates_unchanged_without_completion(self):
        failure = RuntimeError("Gateway unavailable")
        self.gateway.charge.side_effect = failure

        with self.assertRaises(RuntimeError) as raised:
            self.service.process_order("order-id", "customer-id", 49.5)

        self.assertIs(raised.exception, failure)
        self.assert_failed_payment_calls()

    def test_checkout_delegates_payment_to_shared_operation(self):
        self.service.process_payment = Mock(return_value=SimpleNamespace(success=True))

        returned = self.service.process_order("order-id", "customer-id", 49.5)

        self.service.process_payment.assert_called_once_with("customer-token", 49.5)
        self.gateway.charge.assert_not_called()
        self.assertIs(returned, self.order)
        self.assertEqual(self.order.status, "PAID")
        self.db.save_order.assert_called_once_with(self.order)
        self.notifier.send_receipt.assert_called_once_with(self.customer.email, self.order)

    def assert_failed_payment_calls(self):
        self.assertEqual(self.order.status, "PENDING")
        self.assertEqual(self.calls.mock_calls, [
            call.db.get_customer("customer-id"),
            call.db.get_order("order-id"),
            call.gateway.charge("customer-token", 49.5),
        ])


if __name__ == "__main__":
    unittest.main()
