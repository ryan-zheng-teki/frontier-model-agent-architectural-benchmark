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
        
        # 3. Payment execution & state update
        self._charge_and_mark_paid(customer, order, amount)

        # 4. Notification
        self.notification_service.send_receipt(customer.email, order)
        return order

    def process_internal_order(self, order_id: str, customer_id: str, amount: float):
        """Process a pre-verified enterprise payment from a trusted internal caller.

        The caller must enforce enterprise eligibility, validation, fraud scoring,
        and authorization before calling this method. Customer activity and order
        lifecycle checks are skipped, and no customer receipt is sent.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        customer = self.db.get_customer(customer_id)
        if not customer:
            raise ValueError("Invalid customer")

        order = self.db.get_order(order_id)
        if not order:
            raise ValueError("Order does not exist")

        self._charge_and_mark_paid(customer, order, amount)
        return order

    def _charge_and_mark_paid(self, customer, order, amount: float):
        payment_result = self.payment_gateway.charge(customer.payment_token, amount)
        if not payment_result.success:
            raise Exception("Payment failed: " + payment_result.error)

        order.status = "PAID"
        self.db.save_order(order)
