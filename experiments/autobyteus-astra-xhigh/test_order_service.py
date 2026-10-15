import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from order_service import OrderService


class UnusableDependency:
    def __getattr__(self, name):
        raise AssertionError(f"Unexpected dependency access: {name}")


class PaymentTests(unittest.TestCase):
    def setUp(self):
        self.gateway = Mock(spec=["charge"])
        self.service = OrderService(
            UnusableDependency(), self.gateway, UnusableDependency()
        )

    def test_success_returns_exact_result_and_charges_once(self):
        result = SimpleNamespace(success=True)
        self.gateway.charge.return_value = result
        self.assertIs(self.service.process_payment("enterprise-token", 42.5), result)
        self.gateway.charge.assert_called_once_with("enterprise-token", 42.5)

    def test_nonpositive_amount_rejected_before_charge(self):
        for amount in (0, -1):
            with self.subTest(amount=amount):
                with self.assertRaisesRegex(ValueError, "^Amount must be positive$"):
                    self.service.process_payment("enterprise-token", amount)
        self.gateway.charge.assert_not_called()

    def test_unsuccessful_result_uses_existing_exception(self):
        self.gateway.charge.return_value = SimpleNamespace(success=False, error="declined")
        with self.assertRaises(Exception) as raised:
            self.service.process_payment("enterprise-token", 42.5)
        self.assertIs(type(raised.exception), Exception)
        self.assertEqual(str(raised.exception), "Payment failed: declined")
        self.gateway.charge.assert_called_once_with("enterprise-token", 42.5)

    def test_gateway_exception_propagates_unchanged(self):
        error = RuntimeError("gateway unavailable")
        self.gateway.charge.side_effect = error
        with self.assertRaises(RuntimeError) as raised:
            self.service.process_payment("enterprise-token", 42.5)
        self.assertIs(raised.exception, error)
        self.gateway.charge.assert_called_once_with("enterprise-token", 42.5)


class CustomerOrderTests(unittest.TestCase):
    def setUp(self):
        self.customer = SimpleNamespace(
            is_active=True, payment_token="customer-token", email="customer@example.test"
        )
        self.order = SimpleNamespace(status="PENDING")
        self.db = Mock(spec=["get_customer", "get_order", "save_order"])
        self.gateway = Mock(spec=["charge"])
        self.notifications = Mock(spec=["send_receipt"])
        self.db.get_customer.return_value = self.customer
        self.db.get_order.return_value = self.order
        self.gateway.charge.return_value = SimpleNamespace(success=True)
        self.service = OrderService(self.db, self.gateway, self.notifications)
        self.calls = Mock()
        self.calls.attach_mock(self.db, "db")
        self.calls.attach_mock(self.gateway, "gateway")
        self.calls.attach_mock(self.notifications, "notifications")

    def process_order(self, amount=42.5):
        return self.service.process_order("order-id", "customer-id", amount)

    def test_success_preserves_full_sequence_state_and_return_identity(self):
        states = []
        self.gateway.charge.side_effect = lambda *_: (
            states.append(("charge", self.order.status)) or SimpleNamespace(success=True)
        )
        self.db.save_order.side_effect = lambda order: states.append(("save", order.status))
        self.notifications.send_receipt.side_effect = lambda email, order: states.append(
            ("receipt", order.status)
        )
        with patch.object(self.service, "process_payment", wraps=self.service.process_payment) as payment:
            self.assertIs(self.process_order(), self.order)
            payment.assert_called_once_with("customer-token", 42.5)
        self.assertEqual(self.order.status, "PAID")
        self.assertEqual(states, [("charge", "PENDING"), ("save", "PAID"), ("receipt", "PAID")])
        self.assertEqual(self.calls.mock_calls, [
            call.db.get_customer("customer-id"),
            call.db.get_order("order-id"),
            call.gateway.charge("customer-token", 42.5),
            call.db.save_order(self.order),
            call.notifications.send_receipt("customer@example.test", self.order),
        ])

    def test_nonpositive_amount_stops_before_all_dependencies(self):
        for amount in (0, -1):
            with self.subTest(amount=amount):
                with self.assertRaisesRegex(ValueError, "^Amount must be positive$"):
                    self.process_order(amount)
        self.assertEqual(self.calls.mock_calls, [])
        self.assertEqual(self.order.status, "PENDING")

    def test_missing_or_inactive_customer_stops_before_order_lookup(self):
        for customer in (None, SimpleNamespace(is_active=False)):
            with self.subTest(customer=customer):
                self.calls.reset_mock()
                self.db.get_customer.return_value = customer
                with self.assertRaisesRegex(ValueError, "^Invalid or inactive customer$"):
                    self.process_order()
                self.assertEqual(self.calls.mock_calls, [call.db.get_customer("customer-id")])
                self.assertEqual(self.order.status, "PENDING")

    def test_missing_or_nonpending_order_stops_before_charge(self):
        for order in (None, SimpleNamespace(status="PAID")):
            with self.subTest(order=order):
                self.calls.reset_mock()
                self.db.get_order.return_value = order
                with self.assertRaisesRegex(ValueError, "^Order is not in pending state$"):
                    self.process_order()
                self.assertEqual(self.calls.mock_calls, [
                    call.db.get_customer("customer-id"), call.db.get_order("order-id")
                ])
                if order is not None:
                    self.assertEqual(order.status, "PAID")

    def assert_payment_failure_stopped_effects(self):
        self.assertEqual(self.order.status, "PENDING")
        self.assertEqual(self.calls.mock_calls, [
            call.db.get_customer("customer-id"),
            call.db.get_order("order-id"),
            call.gateway.charge("customer-token", 42.5),
        ])

    def test_unsuccessful_payment_stops_before_mutation_save_and_receipt(self):
        self.gateway.charge.return_value = SimpleNamespace(success=False, error="declined")
        with self.assertRaises(Exception) as raised:
            self.process_order()
        self.assertIs(type(raised.exception), Exception)
        self.assertEqual(str(raised.exception), "Payment failed: declined")
        self.assert_payment_failure_stopped_effects()

    def test_gateway_exception_propagates_without_customer_effects(self):
        error = RuntimeError("gateway unavailable")
        self.gateway.charge.side_effect = error
        with self.assertRaises(RuntimeError) as raised:
            self.process_order()
        self.assertIs(raised.exception, error)
        self.assert_payment_failure_stopped_effects()


if __name__ == "__main__":
    unittest.main()
