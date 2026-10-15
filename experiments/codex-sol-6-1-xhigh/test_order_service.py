import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from order_service import OrderService


class OrderServiceTests(unittest.TestCase):
    def setUp(self):
        self.customer = SimpleNamespace(
            is_active=True, payment_token="stored-token", email="billing@example.com"
        )
        self.order = SimpleNamespace(status="PENDING")
        self.db = Mock()
        self.db.get_customer.return_value = self.customer
        self.db.get_order.return_value = self.order
        self.gateway = Mock()
        self.gateway.charge.return_value = SimpleNamespace(success=True)
        self.notifications = Mock()
        self.service = OrderService(self.db, self.gateway, self.notifications)

    def test_customer_checkout_charges_saves_and_sends_receipt(self):
        result = self.service.process_order("order-1", "customer-1", 25)

        self.assertIs(result, self.order)
        self.db.get_customer.assert_called_once_with("customer-1")
        self.db.get_order.assert_called_once_with("order-1")
        self.gateway.charge.assert_called_once_with("stored-token", 25)
        self.assertEqual(self.order.status, "PAID")
        self.db.save_order.assert_called_once_with(self.order)
        self.notifications.send_receipt.assert_called_once_with(
            "billing@example.com", self.order
        )

    def test_internal_payment_accepts_inactive_customer_and_nonpending_order(self):
        self.customer.is_active = False
        self.order.status = "RECURRING"

        result = self.service.process_internal_order("order-1", "customer-1", 25)

        self.assertIs(result, self.order)
        self.db.get_customer.assert_called_once_with("customer-1")
        self.db.get_order.assert_called_once_with("order-1")
        self.gateway.charge.assert_called_once_with("stored-token", 25)
        self.assertEqual(self.order.status, "PAID")
        self.db.save_order.assert_called_once_with(self.order)
        self.notifications.send_receipt.assert_not_called()

    def test_internal_payment_does_not_need_customer_lifecycle_or_contact_fields(self):
        self.db.get_customer.return_value = SimpleNamespace(payment_token="internal-token")
        self.db.get_order.return_value = SimpleNamespace()

        result = self.service.process_internal_order("order-1", "customer-1", 25)

        self.gateway.charge.assert_called_once_with("internal-token", 25)
        self.assertEqual(result.status, "PAID")
        self.db.save_order.assert_called_once_with(result)
        self.notifications.send_receipt.assert_not_called()

    def test_customer_checkout_rejects_inactive_customer(self):
        self.customer.is_active = False

        with self.assertRaisesRegex(ValueError, "Invalid or inactive customer"):
            self.service.process_order("order-1", "customer-1", 25)

        self.gateway.charge.assert_not_called()
        self.db.save_order.assert_not_called()
        self.notifications.send_receipt.assert_not_called()

    def test_customer_checkout_rejects_nonpending_order(self):
        self.order.status = "RECURRING"

        with self.assertRaisesRegex(ValueError, "Order is not in pending state"):
            self.service.process_order("order-1", "customer-1", 25)

        self.gateway.charge.assert_not_called()
        self.db.save_order.assert_not_called()
        self.notifications.send_receipt.assert_not_called()

    def test_both_paths_reject_nonpositive_amounts_before_loading_records(self):
        for method in (self.service.process_order, self.service.process_internal_order):
            for amount in (0, -1):
                with self.subTest(method=method.__name__, amount=amount):
                    with self.assertRaisesRegex(ValueError, "Amount must be positive"):
                        method("order-1", "customer-1", amount)

        self.db.get_customer.assert_not_called()
        self.db.get_order.assert_not_called()
        self.gateway.charge.assert_not_called()
        self.db.save_order.assert_not_called()
        self.notifications.send_receipt.assert_not_called()

    def test_both_paths_require_an_existing_customer_and_order(self):
        for method in (self.service.process_order, self.service.process_internal_order):
            for missing in ("customer", "order"):
                with self.subTest(method=method.__name__, missing=missing):
                    self.db.get_customer.return_value = (
                        None if missing == "customer" else self.customer
                    )
                    self.db.get_order.return_value = (
                        None if missing == "order" else self.order
                    )
                    with self.assertRaises(ValueError):
                        method("order-1", "customer-1", 25)

        self.gateway.charge.assert_not_called()
        self.db.save_order.assert_not_called()
        self.notifications.send_receipt.assert_not_called()

    def test_gateway_rejection_preserves_order_and_skips_receipt_on_both_paths(self):
        self.gateway.charge.return_value = SimpleNamespace(success=False, error="declined")

        for method in (self.service.process_order, self.service.process_internal_order):
            with self.subTest(method=method.__name__):
                with self.assertRaisesRegex(Exception, "Payment failed: declined"):
                    method("order-1", "customer-1", 25)
                self.assertEqual(self.order.status, "PENDING")

        self.assertEqual(self.gateway.charge.call_count, 2)
        self.db.save_order.assert_not_called()
        self.notifications.send_receipt.assert_not_called()

    def test_gateway_exception_preserves_order_and_skips_receipt_on_both_paths(self):
        self.gateway.charge.side_effect = RuntimeError("gateway unavailable")

        for method in (self.service.process_order, self.service.process_internal_order):
            with self.subTest(method=method.__name__):
                with self.assertRaisesRegex(RuntimeError, "gateway unavailable"):
                    method("order-1", "customer-1", 25)
                self.assertEqual(self.order.status, "PENDING")

        self.db.save_order.assert_not_called()
        self.notifications.send_receipt.assert_not_called()


if __name__ == "__main__":
    unittest.main()
