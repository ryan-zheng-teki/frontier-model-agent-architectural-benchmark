"""API/E2E boundary coverage for enterprise-internal-billing.

Unlike test_order_service.py (MagicMock), these tests drive the services through
stateful in-memory fakes of the db / gateway / notifier contracts as visible by
usage (`gateway.charge(token, amount) -> .success/.error`,
`db.get_customer/get_order/save_order`, `notifier.send_receipt(email, order)`).
Fakes record an ordered call log so "before any lookup", "no order read" and
"no receipt" are observed, not assumed.

No git baseline exists, so TC-008 compares `process_order` with a reconstruction
of the ORIGINAL pre-change logic (investigation-notes E-1).
"""
import itertools
import unittest
from types import SimpleNamespace

from order_service import EnterpriseBillingService, OrderService


class Log:
    def __init__(self):
        self.calls = []

    def names(self):
        return [c[0] for c in self.calls]


class FakeDb:
    def __init__(self, log, customers=None, orders=None):
        self.log = log
        self.customers = dict(customers or {})
        self.orders = dict(orders or {})

    def get_customer(self, customer_id):
        self.log.calls.append(("db.get_customer", customer_id))
        return self.customers.get(customer_id)

    def get_order(self, order_id):
        self.log.calls.append(("db.get_order", order_id))
        return self.orders.get(order_id)

    def save_order(self, order):
        self.log.calls.append(("db.save_order", order.id, order.status))
        self.orders[order.id] = order


class FakeGateway:
    """Declines tokens listed in `declines` (token -> error); otherwise succeeds."""

    def __init__(self, log, declines=None):
        self.log = log
        self.declines = dict(declines or {})
        self.charges = []

    def charge(self, token, amount):
        self.log.calls.append(("gateway.charge", token, amount))
        self.charges.append((token, amount))
        if token in self.declines:
            return SimpleNamespace(success=False, error=self.declines[token], reference=None)
        return SimpleNamespace(success=True, error=None, reference="ref-%d" % len(self.charges))


class FakeNotifier:
    def __init__(self, log):
        self.log = log
        self.receipts = []

    def send_receipt(self, email, order):
        self.log.calls.append(("notifier.send_receipt", email, order.id))
        self.receipts.append((email, order.id))


def customer(token, active=True, email="x@y.z"):
    return SimpleNamespace(payment_token=token, is_active=active, email=email)


def order(oid, status="PENDING"):
    return SimpleNamespace(id=oid, status=status)


class EnterpriseChargeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.log = Log()
        self.db = FakeDb(
            self.log,
            customers={
                "ent-inactive": customer("tok-inactive", active=False),
                "ent-active": customer("tok-active", active=True),
                "ent-declined": customer("tok-declined", active=False),
            },
            orders={"o-pending": order("o-pending")},
        )
        self.gw = FakeGateway(self.log, declines={"tok-declined": "insufficient funds"})
        self.svc = EnterpriseBillingService(self.db, self.gw)

    # TC-001 / AC-001
    def test_tc001_inactive_account_charged_with_stored_token(self):
        result = self.svc.charge_account("ent-inactive", 250.0)
        self.assertEqual(self.gw.charges, [("tok-inactive", 250.0)])
        self.assertTrue(result.success)
        self.assertEqual(result.reference, "ref-1")  # gateway result returned as-is

    # TC-002 / AC-002, AC-003
    def test_tc002_no_order_access_no_receipt_dependency(self):
        before = dict(self.db.orders)
        before_status = {k: v.status for k, v in before.items()}
        self.svc.charge_account("ent-inactive", 10.0)
        self.assertEqual(self.log.names(), ["db.get_customer", "gateway.charge"])
        self.assertEqual(self.db.orders, before)
        self.assertEqual({k: v.status for k, v in self.db.orders.items()}, before_status)
        self.assertFalse(hasattr(self.svc, "notification_service"))
        self.assertEqual(self.db.orders["o-pending"].status, "PENDING")

    # TC-003 / AC-004
    def test_tc003_decline_same_error_as_customer_path_and_no_state_change(self):
        with self.assertRaises(Exception) as ent:
            self.svc.charge_account("ent-declined", 5.0)
        # same gateway on the customer path produces the identical failure shape
        self.db.customers["cust"] = customer("tok-declined")
        self.db.orders["o2"] = order("o2")
        with self.assertRaises(Exception) as cust:
            OrderService(self.db, self.gw, FakeNotifier(self.log)).process_order("o2", "cust", 5.0)
        self.assertIs(type(ent.exception), type(cust.exception))
        self.assertEqual(str(ent.exception), "Payment failed: insufficient funds")
        self.assertEqual(str(ent.exception), str(cust.exception))
        self.assertEqual(self.db.orders["o-pending"].status, "PENDING")

    # TC-004 / AC-006
    def test_tc004_non_positive_amount_rejected_before_any_call(self):
        for bad in (0, -1, 0.0, -0.01):
            with self.assertRaisesRegex(ValueError, "^Amount must be positive$"):
                self.svc.charge_account("ent-inactive", bad)
        self.assertEqual(self.log.calls, [])

    # TC-005 / AC-007
    def test_tc005_unknown_account_rejected_without_charge(self):
        with self.assertRaises(ValueError) as cm:
            self.svc.charge_account("no-such-account", 5.0)
        self.assertEqual(str(cm.exception), "Unknown customer account")
        self.assertEqual(self.log.names(), ["db.get_customer"])
        self.assertEqual(self.gw.charges, [])

    # TC-006 / SCN-001, SCN-002, SCN-004: recurring billing job
    def test_tc006_billing_job_mixed_batch(self):
        batch = [
            ("ent-inactive", 100.0),
            ("ent-active", 20.0),
            ("ghost", 7.0),
            ("ent-declined", 3.0),
            ("ent-active", 0),
            ("ent-inactive", 1.5),
        ]
        outcomes = []
        for account, amount in batch:  # the job's own per-account handling
            try:
                self.svc.charge_account(account, amount)
                outcomes.append("ok")
            except ValueError as e:
                outcomes.append("ValueError:" + str(e))
            except Exception as e:
                outcomes.append("Exception:" + str(e))
        self.assertEqual(
            outcomes,
            [
                "ok",
                "ok",
                "ValueError:Unknown customer account",
                "Exception:Payment failed: insufficient funds",
                "ValueError:Amount must be positive",
                "ok",
            ],
        )
        self.assertEqual(
            self.gw.charges,
            [
                ("tok-inactive", 100.0),
                ("tok-active", 20.0),
                ("tok-declined", 3.0),
                ("tok-inactive", 1.5),
            ],
        )
        self.assertNotIn("db.get_order", self.log.names())
        self.assertNotIn("db.save_order", self.log.names())

    # TC-007 / SCN-003 + REQ-005: shared collaborators, mixed traffic
    def test_tc007_customer_and_internal_traffic_share_collaborators(self):
        notifier = FakeNotifier(self.log)
        self.db.customers["cust"] = customer("tok-cust", email="cust@x.y")
        self.db.orders["o-cust"] = order("o-cust")
        orders_svc = OrderService(self.db, self.gw, notifier)

        self.svc.charge_account("ent-inactive", 50.0)
        self.assertEqual(self.db.orders["o-cust"].status, "PENDING")
        self.assertEqual(notifier.receipts, [])

        paid = orders_svc.process_order("o-cust", "cust", 30.0)
        self.assertEqual(paid.status, "PAID")
        self.assertEqual(self.db.orders["o-cust"].status, "PAID")
        self.assertEqual(notifier.receipts, [("cust@x.y", "o-cust")])

        self.svc.charge_account("ent-active", 5.0)
        self.assertEqual(notifier.receipts, [("cust@x.y", "o-cust")])  # no extra receipt
        self.assertEqual(
            self.gw.charges,
            [("tok-inactive", 50.0), ("tok-cust", 30.0), ("tok-active", 5.0)],
        )
        # customer path still refuses the same inactive account (REQ-005 isolation)
        self.db.orders["o-x"] = order("o-x")
        with self.assertRaisesRegex(ValueError, "Invalid or inactive customer"):
            orders_svc.process_order("o-x", "ent-inactive", 1.0)
        self.assertEqual(self.gw.charges[-1], ("tok-active", 5.0))


def original_process_order(db, payment_gateway, notification_service, order_id, customer_id, amount):
    """Reconstruction of the pre-change process_order (investigation-notes E-1)."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    cust = db.get_customer(customer_id)
    if not cust or not cust.is_active:
        raise ValueError("Invalid or inactive customer")
    o = db.get_order(order_id)
    if not o or o.status != "PENDING":
        raise ValueError("Order is not in pending state")
    payment_result = payment_gateway.charge(cust.payment_token, amount)
    if not payment_result.success:
        raise Exception("Payment failed: " + payment_result.error)
    o.status = "PAID"
    db.save_order(o)
    notification_service.send_receipt(cust.email, o)
    return o


class ProcessOrderDifferentialTests(unittest.TestCase):
    """TC-008 / REQ-005 / AC-005: current process_order == original, observed end to end."""

    def _run(self, fn, amount, cust, ord_, declines):
        log = Log()
        db = FakeDb(
            log,
            customers={"c": cust} if cust is not None else {},
            orders={"o": ord_} if ord_ is not None else {},
        )
        gw = FakeGateway(log, declines=declines)
        notifier = FakeNotifier(log)
        try:
            ret = fn(db, gw, notifier, amount)
            outcome = ("returned", ret.status)
        except Exception as e:
            outcome = (type(e).__name__, str(e))
        final_orders = {k: v.status for k, v in db.orders.items()}
        return outcome, log.calls, final_orders, notifier.receipts

    def test_tc008_matrix(self):
        amounts = [10.0, 0, -5, 0.01]
        customers = [None, "inactive", "active"]
        orders = [None, "PENDING", "PAID", "CANCELLED"]
        declines = [{}, {"tok": "card declined"}]
        n = 0
        for amount, ckind, okind, decl in itertools.product(amounts, customers, orders, declines):
            def make(kind):
                if kind is None:
                    return None
                return customer("tok", active=(kind == "active"), email="e@x.y")

            def run(fn):
                # fresh objects per run: process_order mutates the order
                return self._run(
                    fn,
                    amount,
                    make(ckind),
                    order("o", okind) if okind else None,
                    decl,
                )

            new = run(lambda db, gw, nt, a: OrderService(db, gw, nt).process_order("o", "c", a))
            old = run(lambda db, gw, nt, a: original_process_order(db, gw, nt, "o", "c", a))
            self.assertEqual(new, old, msg="mismatch for %r" % ((amount, ckind, okind, decl),))
            n += 1
        self.assertEqual(n, 4 * 3 * 4 * 2)


if __name__ == "__main__":
    unittest.main()
