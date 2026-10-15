def _charge_or_raise(payment_gateway, payment_token, amount):
    """Single owner of "charge the gateway; a declined charge is an error"."""
    payment_result = payment_gateway.charge(payment_token, amount)
    if not payment_result.success:
        raise Exception("Payment failed: " + payment_result.error)
    return payment_result


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
        _charge_or_raise(self.payment_gateway, customer.payment_token, amount)

        # 4. State update & Notification
        order.status = "PAID"
        self.db.save_order(order)
        self.notification_service.send_receipt(customer.email, order)
        return order


class EnterpriseBillingService:
    """Payment entry point for TRUSTED INTERNAL callers only (recurring
    subscription billing jobs, administrative batch tasks) charging
    pre-verified corporate enterprise accounts.

    The caller owns validation and fraud scoring. This service deliberately
    does NOT run the customer-active check or the pending-order check, does
    not read or update the order record, and sends no customer receipt.
    It must never be wired into customer-facing request handlers; those use
    OrderService.process_order.

    Retries are the caller's responsibility to make safe: the pending-order
    check that used to stop a second charge for the same order is not run here.
    """

    def __init__(self, db, payment_gateway):
        self.db = db
        self.payment_gateway = payment_gateway

    def charge_account(self, customer_id: str, amount: float):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        # Lookup is only to obtain the stored payment token; is_active is
        # intentionally not consulted.
        customer = self.db.get_customer(customer_id)
        if not customer:
            raise ValueError("Unknown customer account")
        return _charge_or_raise(self.payment_gateway, customer.payment_token, amount)
