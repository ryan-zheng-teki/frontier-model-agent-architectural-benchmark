"""Internal Enterprise Billing Service.

Dedicated service for internal recurring subscription billing jobs and administrative
batch tasks to process payments for pre-verified corporate enterprise accounts.
"""

import logging
import math
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PaymentFailedError(Exception):
    """Raised when the payment gateway declines or fails a charge."""
    pass


class InternalBillingService:
    """Processes payments for pre-verified corporate enterprise accounts.

    Architectural Boundary:
    - Dedicated to internal trusted callers (subscription billing jobs, batch tasks).
    - Upstream systems have already completed validation and fraud scoring.
    - Operates outside the standard customer retail order lifecycle (no order records,
      no order status transitions, no customer receipt emails).
    - Injected only at trusted internal composition roots; never exposed to public
      or customer-facing checkout endpoints.
    """

    def __init__(self, db: Any, payment_gateway: Any):
        """Initialize InternalBillingService with segregated dependencies.

        Note: Intentionally does NOT accept or depend on notification_service,
        as enterprise batch billing does not issue customer checkout receipts.
        """
        self.db = db
        self.payment_gateway = payment_gateway

    def charge_enterprise_account(
        self,
        account_id: str,
        amount: float,
        reference: Optional[str] = None,
        requested_by: Optional[str] = None,
    ) -> Any:
        """Charge a pre-verified corporate enterprise account.

        Args:
            account_id: Identifier of the corporate enterprise account.
            amount: Positive numeric amount to charge.
            reference: Optional idempotency key or batch job correlation reference.
            requested_by: Optional name/ID of internal job or service initiating charge.

        Returns:
            Payment gateway charge result.

        Raises:
            ValueError: If amount is non-positive / invalid or account has no payment token.
            PaymentFailedError: If payment gateway charge fails or is declined.
        """
        if not account_id:
            raise ValueError("account_id is required")

        if not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount <= 0:
            self._audit(
                status="REJECTED",
                account_id=account_id,
                amount=amount,
                reference=reference,
                requested_by=requested_by,
                reason="Amount must be a positive finite number",
            )
            raise ValueError("Amount must be positive")

        # Retrieve enterprise account record to obtain stored payment token.
        # Customer status (is_active) check is deliberately omitted because
        # corporate enterprise accounts are pre-verified upstream.
        account = self.db.get_customer(account_id)
        token = getattr(account, "payment_token", None) if account else None
        if not token:
            self._audit(
                status="REJECTED",
                account_id=account_id,
                amount=amount,
                reference=reference,
                requested_by=requested_by,
                reason="Unknown enterprise account or missing payment token",
            )
            raise ValueError("Invalid enterprise account or missing payment token")

        # Execute payment through gateway
        payment_result = self.payment_gateway.charge(token, amount)
        if not getattr(payment_result, "success", False):
            error_message = getattr(payment_result, "error", "Unknown gateway error")
            self._audit(
                status="FAILED",
                account_id=account_id,
                amount=amount,
                reference=reference,
                requested_by=requested_by,
                reason=str(error_message),
            )
            raise PaymentFailedError(f"Payment failed: {error_message}")

        self._audit(
            status="SUCCESS",
            account_id=account_id,
            amount=amount,
            reference=reference,
            requested_by=requested_by,
        )
        return payment_result

    def process_payment(
        self,
        account_id: str,
        amount: float,
        reference: Optional[str] = None,
        requested_by: Optional[str] = None,
    ) -> Any:
        """Alias for charge_enterprise_account for intuitive caller ergonomics."""
        return self.charge_enterprise_account(
            account_id=account_id,
            amount=amount,
            reference=reference,
            requested_by=requested_by,
        )

    @staticmethod
    def _audit(
        status: str,
        account_id: str,
        amount: Any,
        reference: Optional[str],
        requested_by: Optional[str],
        reason: str = "",
    ) -> None:
        logger.info(
            "internal_billing_event status=%s account_id=%s amount=%s reference=%s requested_by=%s reason=%s",
            status,
            account_id,
            amount,
            reference,
            requested_by,
            reason,
        )
