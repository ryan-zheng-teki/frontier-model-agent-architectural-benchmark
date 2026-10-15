class OrderService:
    def __init__(self, db, payment_gateway, notification_service):
        self.db = db
        self.payment_gateway = payment_gateway
        self.notification_service = notification_service

    def process_payment(self, payment_token: str, amount: float):
        """Charge a trusted caller's payment token and return the gateway result.

        Callers are responsible for account eligibility, authorization, fraud
        screening, and any order lifecycle or notification work.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        payment_result = self.payment_gateway.charge(payment_token, amount)
        if not payment_result.success:
            raise Exception("Payment failed: " + payment_result.error)
        return payment_result

    def process_order(self, order_id: str, customer_id: str, amount: float):
        # 1. Validation
        # Reject invalid amounts before accessing the database.
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
