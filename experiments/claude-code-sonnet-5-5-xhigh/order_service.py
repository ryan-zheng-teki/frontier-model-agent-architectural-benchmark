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


    def process_internal_payment(self, reference_id: str, customer_id: str, amount: float, caller: str):
        """Charge a pre-verified enterprise account on behalf of an internal job.

        INTERNAL USE ONLY (billing jobs, admin batch tasks). Do not expose to
        customer-facing endpoints. The caller is responsible for upstream
        validation and fraud scoring. Unlike process_order, this skips the
        customer-active check, the order-PENDING check and the customer receipt.
        It does not read or modify order state.
        """
        if not caller:
            raise ValueError("Internal caller identity is required")
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Needed only to obtain the payment token; no status checks.
        customer = self.db.get_customer(customer_id)
        if not customer:
            raise ValueError("Customer not found")

        logger.info("internal payment: caller=%s ref=%s customer=%s amount=%s",
                    caller, reference_id, customer_id, amount)
        payment_result = self.payment_gateway.charge(customer.payment_token, amount)
        if not payment_result.success:
            logger.warning("internal payment failed: caller=%s ref=%s error=%s",
                           caller, reference_id, payment_result.error)
            raise Exception("Payment failed: " + payment_result.error)
        logger.info("internal payment succeeded: caller=%s ref=%s", caller, reference_id)
        return payment_result
