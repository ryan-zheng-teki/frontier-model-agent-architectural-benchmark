class OrderService:
    def __init__(self, db, payment_gateway, notification_service):
        self.db = db
        self.payment_gateway = payment_gateway
        self.notification_service = notification_service

    def process_payment(self, payment_token: str, amount: float):
        """Charge a trusted, upstream-verified caller's payment token.

        Return the successful gateway result without customer/order access or
        receipt notification. Authorization and fraud checks belong upstream.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        payment_result = self.payment_gateway.charge(payment_token, amount)
        if not payment_result.success:
            raise Exception("Payment failed: " + payment_result.error)
        return payment_result

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
        self.process_payment(customer.payment_token, amount)

        # 4. State update & Notification
        order.status = "PAID"
        self.db.save_order(order)
        self.notification_service.send_receipt(customer.email, order)
        return order
