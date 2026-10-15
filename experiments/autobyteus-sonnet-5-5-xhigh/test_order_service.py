import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from order_service import EnterpriseBillingService, OrderService


def _gateway(success=True, error="declined"):
    gw = MagicMock()
    gw.charge.return_value = SimpleNamespace(success=success, error=error)
    return gw


class ProcessOrderPreservedTests(unittest.TestCase):
    """process_order behavior must be unchanged (REQ-005)."""

    def setUp(self):
        self.customer = SimpleNamespace(is_active=True, payment_token="tok", email="a@b.c")
        self.order = SimpleNamespace(status="PENDING")
        self.db = MagicMock()
        self.db.get_customer.return_value = self.customer
        self.db.get_order.return_value = self.order
        self.notifier = MagicMock()

    def test_happy_path(self):
        gw = _gateway()
        svc = OrderService(self.db, gw, self.notifier)
        result = svc.process_order("o1", "c1", 10.0)
        self.assertEqual(result.status, "PAID")
        gw.charge.assert_called_once_with("tok", 10.0)
        self.db.save_order.assert_called_once_with(self.order)
        self.notifier.send_receipt.assert_called_once_with("a@b.c", self.order)

    def test_inactive_customer_rejected(self):
        self.customer.is_active = False
        gw = _gateway()
        with self.assertRaisesRegex(ValueError, "Invalid or inactive customer"):
            OrderService(self.db, gw, self.notifier).process_order("o1", "c1", 10.0)
        gw.charge.assert_not_called()

    def test_non_pending_order_rejected(self):
        self.order.status = "PAID"
        gw = _gateway()
        with self.assertRaisesRegex(ValueError, "not in pending state"):
            OrderService(self.db, gw, self.notifier).process_order("o1", "c1", 10.0)
        gw.charge.assert_not_called()

    def test_declined_payment(self):
        svc = OrderService(self.db, _gateway(success=False, error="nope"), self.notifier)
        with self.assertRaisesRegex(Exception, "Payment failed: nope"):
            svc.process_order("o1", "c1", 10.0)
        self.db.save_order.assert_not_called()
        self.notifier.send_receipt.assert_not_called()


class EnterpriseBillingTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.db.get_customer.return_value = SimpleNamespace(
            is_active=False, payment_token="ent-tok", email="corp@x.y"
        )

    def test_charges_without_status_or_order_checks_or_receipt(self):
        gw = _gateway()
        result = EnterpriseBillingService(self.db, gw).charge_account("ent1", 99.5)
        gw.charge.assert_called_once_with("ent-tok", 99.5)  # inactive flag ignored
        self.assertTrue(result.success)
        self.db.get_order.assert_not_called()
        self.db.save_order.assert_not_called()

    def test_declined_payment_raises(self):
        svc = EnterpriseBillingService(self.db, _gateway(success=False, error="insufficient"))
        with self.assertRaisesRegex(Exception, "Payment failed: insufficient"):
            svc.charge_account("ent1", 5.0)

    def test_non_positive_amount_rejected_before_any_lookup_or_charge(self):
        gw = _gateway()
        for bad in (0, -1):
            with self.assertRaisesRegex(ValueError, "Amount must be positive"):
                EnterpriseBillingService(self.db, gw).charge_account("ent1", bad)
        self.db.get_customer.assert_not_called()
        gw.charge.assert_not_called()

    def test_unknown_account_rejected_without_charging(self):
        self.db.get_customer.return_value = None
        gw = _gateway()
        with self.assertRaisesRegex(ValueError, "Unknown customer account"):
            EnterpriseBillingService(self.db, gw).charge_account("nope", 5.0)
        gw.charge.assert_not_called()

    def test_has_no_notification_dependency(self):
        svc = EnterpriseBillingService(self.db, _gateway())
        self.assertFalse(hasattr(svc, "notification_service"))


if __name__ == "__main__":
    unittest.main()
