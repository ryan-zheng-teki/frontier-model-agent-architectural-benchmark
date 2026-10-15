class OrderService:
    def __init__(self, db, payment_gateway, notification_service):
        self.db = db
        self.payment_gateway = payment_gateway
        self.notification_service = notification_service

    def process_order(self, order_id: str, customer_id: str, amount: float, is_internal: bool = False):
        # 1. Validation
        if amount <= 0:
            raise ValueError("Amount must be positive")
        customer = self.db.get_customer(customer_id)
        if not is_internal:
            if not customer or not customer.is_active:
                raise ValueError("Invalid or inactive customer")
        
        # 2. State verification
        order = self.db.get_order(order_id)
        if not is_internal:
            if not order or order.status != "PENDING":
                raise ValueError("Order is not in pending state")
        
        # 3. Payment Execution
        payment_result = self.payment_gateway.charge(customer.payment_token, amount)
        if not payment_result.success:
            raise Exception("Payment failed: " + payment_result.error)
        
        # 4. State update & Notification
        order.status = "PAID"
        self.db.save_order(order)
        if not is_internal:
            self.notification_service.send_receipt(customer.email, order)
        return order
