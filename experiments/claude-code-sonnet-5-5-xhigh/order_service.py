import logging

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, db, payment_gateway, notification_service):
        self.db = db
        self.payment_gateway = payment_gateway
        self.notification_service = notification_service

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

        # 3. Payment Execution
        payment_result = self.payment_gateway.charge(customer.payment_token, amount)
        if not payment_result.success:
            raise Exception("Payment failed: " + payment_result.error)

        # 4. State update & Notification
        order.status = "PAID"
        self.db.save_order(order)
        self.notification_service.send_receipt(customer.email, order)
        return order

    def process_internal_payment(
        self, order_id: str, customer_id: str, amount: float, *, initiated_by: str
    ):
        """Charge a pre-verified enterprise account on behalf of an internal job.

        For internal callers only (recurring subscription billing, admin batch
        tasks) that perform their own validation and fraud scoring upstream.
        Unlike process_order, this skips the customer active-status check, the
        PENDING order-state check, and the customer receipt notification.
        Must not be exposed to customer-facing request paths. See DESIGN.md.
        """
        if not initiated_by:
            raise ValueError("initiated_by is required for internal payments")

        # 1. Validation (amount and record existence are still enforced)
        if amount <= 0:
            raise ValueError("Amount must be positive")
        customer = self.db.get_customer(customer_id)
        if not customer:
            raise ValueError("Customer not found")
        order = self.db.get_order(order_id)
        if not order:
            raise ValueError("Order not found")

        # 2. Payment Execution
        logger.info(
            "Internal payment requested by %s: order=%s customer=%s amount=%s prior_status=%s",
            initiated_by, order_id, customer_id, amount, order.status,
        )
        payment_result = self.payment_gateway.charge(customer.payment_token, amount)
        if not payment_result.success:
            logger.warning(
                "Internal payment failed for order=%s (initiated_by=%s): %s",
                order_id, initiated_by, payment_result.error,
            )
            raise Exception("Payment failed: " + str(payment_result.error))

        # 3. State update (no customer receipt)
        order.status = "PAID"
        self.db.save_order(order)
        return order
