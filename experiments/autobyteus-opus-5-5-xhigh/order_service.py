class OrderService:
    def __init__(self, db, payment_gateway, notification_service):
        self.db = db
        self.payment_gateway = payment_gateway
        self.notification_service = notification_service

    def process_order(self, order_id: str, customer_id: str, amount: float):
        """Customer checkout: pay a PENDING order for an active customer and send a receipt."""
        # 1. Validation
        self._require_positive_amount(amount)
        customer = self.db.get_customer(customer_id)
        if not customer or not customer.is_active:
            raise ValueError("Invalid or inactive customer")

        # 2. State verification
        order = self.db.get_order(order_id)
        if not order or order.status != "PENDING":
            raise ValueError("Order is not in pending state")

        # 3. Payment execution & state update
        self._charge_and_mark_paid(customer, order, amount)

        # 4. Notification
        self.notification_service.send_receipt(customer.email, order)
        return order

    def process_internal_enterprise_payment(self, order_id: str, customer_id: str, amount: float):
        """Internal billing jobs and admin batch tasks only; never call from customer-facing code.

        Charges a pre-verified enterprise account for an order in any status.
        Skips the customer active check, the PENDING check and the receipt;
        callers own account validation, fraud scoring, retries and idempotency.
        See DESIGN.md, "Payment Entry Points".
        """
        self._require_positive_amount(amount)
        customer = self.db.get_customer(customer_id)
        if not customer:
            raise ValueError("Customer not found")
        order = self.db.get_order(order_id)
        if not order:
            raise ValueError("Order not found")
        self._charge_and_mark_paid(customer, order, amount)
        return order

    def _require_positive_amount(self, amount: float):
        if amount <= 0:
            raise ValueError("Amount must be positive")

    def _charge_and_mark_paid(self, customer, order, amount: float):
        payment_result = self.payment_gateway.charge(customer.payment_token, amount)
        if not payment_result.success:
            raise Exception("Payment failed: " + payment_result.error)
        order.status = "PAID"
        self.db.save_order(order)
