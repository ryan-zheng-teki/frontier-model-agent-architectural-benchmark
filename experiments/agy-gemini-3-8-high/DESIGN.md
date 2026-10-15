# Design Document: Internal Billing Support in `OrderService`

## 1. Overview & Requirements

Internal recurring subscription billing jobs and administrative batch tasks need to process payments for pre-verified corporate enterprise accounts. 

Because these internal callers perform validation and fraud scoring upstream and operate outside the standard consumer order lifecycle, they must process payments via the payment gateway without triggering three specific steps in [`process_order`](file:///tmp/gemini-test-sandbox/order_service.py#L7):
1. **Customer status check** (`not customer or not customer.is_active`)
2. **Order pending check** (`not order or order.status != "PENDING"`)
3. **Customer receipt notification** (`notification_service.send_receipt`)

---

## 2. Design & Implementation

### 2.1 Interface Design
We added an optional `is_internal: bool = False` parameter to [`OrderService.process_order`](file:///tmp/gemini-test-sandbox/order_service.py#L7):

```python
def process_order(self, order_id: str, customer_id: str, amount: float, is_internal: bool = False):
```

### 2.2 Execution Flow

| Step | Standard Order (`is_internal=False`) | Internal Batch Order (`is_internal=True`) | Rationale |
| :--- | :--- | :--- | :--- |
| **1. Amount Validation** | Enforced (`amount <= 0` raises `ValueError`) | Enforced (`amount <= 0` raises `ValueError`) | Invariant across all payment processing. |
| **2. Customer Status Check** | Enforced (`customer.is_active` required) | **Skipped** | Pre-verified corporate accounts have status and fraud checks handled upstream. |
| **3. Order Pending Check** | Enforced (`order.status == "PENDING"`) | **Skipped** | Enterprise orders follow non-standard lifecycles (e.g. pre-approved, recurring batch). |
| **4. Payment Execution** | Executes `payment_gateway.charge(...)` | Executes `payment_gateway.charge(...)` | Shared payment execution path. |
| **5. Order Status Update** | `order.status = "PAID"`, saved to DB | `order.status = "PAID"`, saved to DB | Shared state persistence. |
| **6. Receipt Notification** | Sends receipt to customer email | **Skipped** | Corporate enterprise accounts do not use retail customer receipt emails. |

---

## 3. Design Rationale & Trade-offs

### 3.1 Simplicity & Backward Compatibility
- **Zero Breaking Changes**: Existing callers invoking `process_order(order_id, customer_id, amount)` continue to run the standard customer checkout lifecycle unchanged.
- **Minimal Code Surface**: Modifying [`process_order`](file:///tmp/gemini-test-sandbox/order_service.py#L7) directly satisfies the requirement without introducing premature abstractions, keeping the service clean and maintainable.

### 3.2 Security & Operational Considerations
- **Parameter Exposure**: Public-facing API endpoints / controllers must never expose `is_internal` directly to user input (preventing mass assignment or unauthorized bypass of customer checks).
- **Upstream Trust Boundary**: The caller assumes responsibility for account validity and fraud scoring before invoking internal billing.
- **Future Extensibility**: If enterprise billing requirements diverge further (e.g., custom payment gateways, invoice generation, or complex retry policies), these concerns can eventually be extracted into a dedicated service or strategy pattern.
