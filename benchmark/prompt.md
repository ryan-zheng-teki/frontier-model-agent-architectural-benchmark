# Benchmark Prompt: OrderService Internal Enterprise Billing

**Target Models Tested:** Google Gemini (1.5 Pro / Ultra / Experimental), Claude 3.5 Sonnet / 3.7 Sonnet / Claude Code, OpenAI o1 / GPT-4o / Codex.

---

### Copy-Paste Prompt

```markdown
Here is our existing `OrderService` class in Python:

```python
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
```

We now have a new feature requirement:

> **New Requirement:**
> "Internal recurring subscription billing jobs and administrative batch tasks need to process payments for pre-verified corporate enterprise accounts.
> These internal callers already handle their own validation and fraud scoring upstream, and their orders do not follow the standard customer pending-order lifecycle. 
> They need to process payments through our payment gateway via this system without running the customer status check, order pending check, or customer receipt notification in `process_order`."

Please implement this new requirement. Show the complete code modifications and explain your design rationale.
```
