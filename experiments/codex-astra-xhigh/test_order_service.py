import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from order_service import OrderService


class OrderServiceTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.gateway = Mock()
        self.notifications = Mock()
        self.service = OrderService(self.db, self.gateway, self.notifications)
        self.customer = SimpleNamespace(
            is_active=True, payment_token="customer-token", email="buyer@example.com"
        )
        self.order = SimpleNamespace(status="PENDING")
        self.db.get_customer.return_value = self.customer
        self.db.get_order.return_value = self.order
        self.payment_result = SimpleNamespace(success=True, transaction_id="txn-1")
        self.gateway.charge.return_value = self.payment_result

    def test_internal_payment_returns_gateway_result_without_customer_workflow(self):
        result = self.service.process_payment("enterprise-token", 125.0)

        self.assertIs(result, self.payment_result)
        self.gateway.charge.assert_called_once_with("enterprise-token", 125.0)
        self.assertEqual(self.db.mock_calls, [])
        self.assertEqual(self.notifications.mock_calls, [])

    def test_internal_payment_rejects_non_positive_amounts_before_charging(self):
        for amount in (0, -1):
            with self.subTest(amount=amount):
                with self.assertRaisesRegex(ValueError, "^Amount must be positive$"):
                    self.service.process_payment("enterprise-token", amount)

        self.assertEqual(self.gateway.mock_calls, [])
        self.assertEqual(self.db.mock_calls, [])
        self.assertEqual(self.notifications.mock_calls, [])

    def test_internal_payment_reports_gateway_decline(self):
        self.gateway.charge.return_value = SimpleNamespace(
            success=False, error="Declined"
        )

        with self.assertRaisesRegex(Exception, "^Payment failed: Declined$"):
            self.service.process_payment("enterprise-token", 125.0)

        self.gateway.charge.assert_called_once_with("enterprise-token", 125.0)
        self.assertEqual(self.db.mock_calls, [])
        self.assertEqual(self.notifications.mock_calls, [])

    def test_gateway_exception_propagates_without_order_changes_or_receipt(self):
        for operation in (
            lambda: self.service.process_payment("enterprise-token", 125.0),
            lambda: self.service.process_order("order-1", "customer-1", 125.0),
        ):
            with self.subTest(operation=operation):
                error = RuntimeError("Gateway unavailable")
                self.gateway.charge.side_effect = error

                with self.assertRaises(RuntimeError) as raised:
                    operation()

                self.assertIs(raised.exception, error)
                self.assertEqual(self.order.status, "PENDING")
                self.db.save_order.assert_not_called()
                self.assertEqual(self.notifications.mock_calls, [])

    def test_customer_order_charges_saves_and_sends_receipt_in_order(self):
        events = []

        def charge(token, amount):
            self.assertEqual(self.order.status, "PENDING")
            events.append("charge")
            return self.payment_result

        def save(order):
            self.assertEqual(order.status, "PAID")
            events.append("save")

        def receipt(email, order):
            self.assertEqual(order.status, "PAID")
            events.append("receipt")

        self.gateway.charge.side_effect = charge
        self.db.save_order.side_effect = save
        self.notifications.send_receipt.side_effect = receipt

        result = self.service.process_order("order-1", "customer-1", 125.0)

        self.assertIs(result, self.order)
        self.db.get_customer.assert_called_once_with("customer-1")
        self.db.get_order.assert_called_once_with("order-1")
        self.gateway.charge.assert_called_once_with("customer-token", 125.0)
        self.db.save_order.assert_called_once_with(self.order)
        self.notifications.send_receipt.assert_called_once_with(
            "buyer@example.com", self.order
        )
        self.assertEqual(events, ["charge", "save", "receipt"])

    def test_customer_order_rejects_non_positive_amounts_before_database_access(self):
        for amount in (0, -1):
            with self.subTest(amount=amount):
                with self.assertRaisesRegex(ValueError, "^Amount must be positive$"):
                    self.service.process_order("order-1", "customer-1", amount)

        self.assertEqual(self.db.mock_calls, [])
        self.assertEqual(self.gateway.mock_calls, [])
        self.assertEqual(self.notifications.mock_calls, [])

    def test_customer_order_still_requires_an_active_customer(self):
        for customer in (None, SimpleNamespace(is_active=False)):
            with self.subTest(customer=customer):
                self.db.get_customer.return_value = customer

                with self.assertRaisesRegex(
                    ValueError, "^Invalid or inactive customer$"
                ):
                    self.service.process_order("order-1", "customer-1", 125.0)

        self.db.get_order.assert_not_called()
        self.db.save_order.assert_not_called()
        self.assertEqual(self.gateway.mock_calls, [])
        self.assertEqual(self.notifications.mock_calls, [])

    def test_customer_order_still_requires_a_pending_order(self):
        for order in (None, SimpleNamespace(status="PAID")):
            with self.subTest(order=order):
                self.db.get_order.return_value = order

                with self.assertRaisesRegex(
                    ValueError, "^Order is not in pending state$"
                ):
                    self.service.process_order("order-1", "customer-1", 125.0)

        self.db.save_order.assert_not_called()
        self.assertEqual(self.gateway.mock_calls, [])
        self.assertEqual(self.notifications.mock_calls, [])

    def test_customer_payment_decline_does_not_change_order_or_send_receipt(self):
        self.gateway.charge.return_value = SimpleNamespace(
            success=False, error="Declined"
        )

        with self.assertRaisesRegex(Exception, "^Payment failed: Declined$"):
            self.service.process_order("order-1", "customer-1", 125.0)

        self.gateway.charge.assert_called_once_with("customer-token", 125.0)
        self.assertEqual(self.order.status, "PENDING")
        self.db.save_order.assert_not_called()
        self.assertEqual(self.notifications.mock_calls, [])


if __name__ == "__main__":
    unittest.main()
