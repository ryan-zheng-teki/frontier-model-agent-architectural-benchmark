# Payment execution independent of the customer order lifecycle

## Decision
Expose `OrderService.process_payment(payment_token, amount)` as the payment-only operation. It validates a positive amount, invokes `payment_gateway.charge(token, amount)` once, raises the existing payment-failure exception for unsuccessful results, and returns the successful gateway result unchanged.

`process_order(order_id, customer_id, amount)` remains the customer workflow. It retains its early amount validation, active-customer check, pending-order check, paid-state persistence, receipt, and returned order. Its gateway execution delegates to `process_payment`, giving both workflows one charge/failure-handling implementation.

The early amount check remains in `process_order` so invalid amounts still fail before database access. The payment-only boundary also enforces this inexpensive invariant; it does not repeat account validation or fraud scoring.

## Internal usage and trust boundary

```python
# Called only after the job has authorized and verified the enterprise account.
result = order_service.process_payment(enterprise_payment_token, invoice_amount)
# The caller owns subscription/batch accounting and lifecycle updates.
```

The method does not fetch customers or orders, inspect their status, change or save an order, or send a receipt. Internal callers supply the gateway token obtained upstream; no synthetic pending order is required. Existing constructor dependencies remain unchanged, but the payment-only operation does not access the database or notification service.

This is an in-process capability for trusted callers, **not an authorization mechanism**. It does not verify corporate membership itself. Do not expose it directly as a customer-controlled endpoint. Eligibility, authorization, validation and fraud scoring remain upstream, as required. Ordinary customer requests continue through `process_order`.

## Why this shape

- Payment execution and customer order orchestration have different responsibilities and return values. Separate operations make that distinction explicit.
- Flags such as `skip_validation`, `skip_pending_check`, or `send_receipt=False` would multiply workflow combinations and make accidental bypass easier.
- Copying gateway logic into a special enterprise method would allow error handling to drift.
- A subclass, strategy framework, or separate service hierarchy is unnecessary for this one-class module; a focused method extraction provides the required reusable boundary.
- The existing customer workflow is still supported behavior, not a legacy fallback. Both callers share one implementation of payment execution.

## Failures and limits

Nonpositive amounts raise `ValueError("Amount must be positive")`. A failed gateway result raises `Exception("Payment failed: " + result.error)`. Gateway exceptions propagate unchanged. No retries are introduced: a retry could charge twice without a gateway idempotency contract. Failed payments must not advance customer order state or send receipts.

No persistence migration, enterprise identity model, scheduler, batch loop, HTTP endpoint, currency conversion, or change to existing save/receipt failure recovery is included. Real gateway settlement is outside local tests.

## Verification

Focused tests should establish payment-only success and failure with no DB/notification interactions, exact token/amount forwarding, positive-amount enforcement, and unchanged gateway exception propagation. Regression tests should establish existing customer validation ordering/messages, successful charge/save/receipt ordering and returned order, plus absence of state changes or notifications after failed payment.

Run the focused stdlib suite from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service
```

`test_order_service.py` covers these contracts with injected fakes/mocks; it does not contact a real gateway.
