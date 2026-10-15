import logging
import math

logger = logging.getLogger(__name__)


class PaymentFailedError(Exception):
    """The payment gateway declined or failed a charge."""


class InternalBillingService:
    """Charges pre-verified enterprise accounts for trusted internal callers.

    The caller has already validated the account and scored fraud upstream.
    This service deliberately does NOT check customer status, read/write orders,
    or send receipts.
    
    Architectural boundary rule: This service must only be instantiated in
    internal worker / batch composition roots and must never be wired into
    customer-facing checkout flows.
    """

    def __init__(self, db, payment_gateway):
        self.db = db
        self.payment_gateway = payment_gateway

    def charge_enterprise_account(self, account_id: str, amount: float, requested_by: str):
        if not requested_by:
            raise ValueError("requested_by is required")
        if not math.isfinite(amount) or amount <= 0:
            self._audit("REJECTED", requested_by, account_id, amount, "invalid amount")
            raise ValueError("Amount must be a finite positive number")

        account = self.db.get_customer(account_id)  # token only; is_active is NOT checked
        token = getattr(account, "payment_token", None)
        if not token:
            self._audit("REJECTED", requested_by, account_id, amount, "unknown account or no payment token")
            raise ValueError("Unknown enterprise account or no payment token")

        result = self.payment_gateway.charge(token, amount)
        if not result.success:
            self._audit("DECLINED", requested_by, account_id, amount, str(result.error))
            raise PaymentFailedError(f"Payment failed: {result.error}")

        self._audit("CHARGED", requested_by, account_id, amount)
        return result

    @staticmethod
    def _audit(outcome: str, requested_by: str, account_id: str, amount: float, detail: str = ""):
        logger.info(
            "internal_charge outcome=%s requested_by=%s account_id=%s amount=%s detail=%s",
            outcome, requested_by, account_id, amount, detail,
        )
