import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    """Raised when the gateway declines or fails a charge.
    Subclasses Exception, so existing `except Exception` callers keep working."""


class UnauthorizedInternalCallerError(PermissionError):
    """Raised when a caller is not registered for the internal payment path."""


@dataclass(frozen=True)
class InternalPaymentRequest:
    caller_id: str        # e.g. "subscription-billing-job"; must be in the allowlist
    account_id: str       # pre-verified corporate account
    amount: float
    idempotency_key: str  # e.g. f"sub-{subscription_id}-{billing_period}"
    reference: str        # free-form trace info (batch run id, invoice number, ...)


class OrderService:
    def __init__(self, db, payment_gateway, notification_service,
                 internal_callers: frozenset = frozenset()):
        self.db = db
        self.payment_gateway = payment_gateway
        self.notification_service = notification_service
        # Empty by default: the internal path stays disabled until explicitly configured.
        self._internal_callers = frozenset(internal_callers)

    # ------------------------------------------------------------------
    # Standard customer flow (behavior unchanged)
    # ------------------------------------------------------------------
    def process_order(self, order_id: str, customer_id: str, amount: float):
        # 1. Validation
        if amount <= 0:
            raise ValueError("Amount must be positive")
        customer = self.db.get_customer(customer_id)
        if not customer or not customer.is_active:
            raise ValueError("Invalid or inactive customer")

        # 2. State verification
        order = self.db.get_order(order_id)
        if not order or order.status != "PENDING":
            raise ValueError("Order is not in pending state")

        # 3. Payment execution
        self._charge(customer.payment_token, amount)

        # 4. State update & notification
        order.status = "PAID"
        self.db.save_order(order)
        self.notification_service.send_receipt(customer.email, order)
        return order

    # ------------------------------------------------------------------
    # Internal flow: recurring billing / admin batch jobs
    # ------------------------------------------------------------------
    def process_internal_payment(self, request: InternalPaymentRequest):
        """Charge a pre-verified corporate account on behalf of an internal caller.

        Intentionally skips: customer status check, order PENDING check,
        order status update, and customer receipt notification.
        """
        if request.caller_id not in self._internal_callers:
            raise UnauthorizedInternalCallerError(
                f"Caller '{request.caller_id}' is not registered for internal payments"
            )

        # Cheap sanity checks that protect the gateway call itself.
        if request.amount <= 0:
            raise ValueError("Amount must be positive")
        if not request.idempotency_key:
            raise ValueError("idempotency_key is required")

        # We need the stored payment method, but we do not evaluate account status.
        account = self.db.get_customer(request.account_id)
        payment_token = getattr(account, "payment_token", None)
        if not payment_token:
            raise ValueError("No payment method on file for account")

        log_ctx = {
            "caller_id": request.caller_id,
            "account_id": request.account_id,
            "amount": request.amount,
            "idempotency_key": request.idempotency_key,
            "reference": request.reference,
        }
        logger.info("internal_payment_attempt", extra=log_ctx)
        try:
            result = self._charge(payment_token, request.amount, request.idempotency_key)
        except PaymentError:
            logger.warning("internal_payment_failed", extra=log_ctx)
            raise
        logger.info("internal_payment_succeeded", extra=log_ctx)
        return result

    # ------------------------------------------------------------------
    # Shared payment step
    # ------------------------------------------------------------------
    def _charge(self, payment_token: str, amount: float,
                idempotency_key: Optional[str] = None):
        kwargs = {} if idempotency_key is None else {"idempotency_key": idempotency_key}
        result = self.payment_gateway.charge(payment_token, amount, **kwargs)
        if not result.success:
            raise PaymentError("Payment failed: " + result.error)
        return result
