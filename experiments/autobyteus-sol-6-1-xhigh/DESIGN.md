# Payment execution without customer-order orchestration

## Decision
Expose `OrderService.process_payment(payment_token: str, amount: float)` for
trusted internal subscription billing jobs and administrative batch tasks.
It validates that the amount is positive, calls the existing gateway once,
raises the existing payment failure on rejection, and returns the successful
gateway result. Gateway exceptions propagate unchanged.

`process_payment` does not fetch customers or orders, check customer activity or
PENDING status, mutate/save orders, or send receipts. Upstream callers own
enterprise eligibility, authorization, validation/fraud scoring, token
resolution and their own billing/task lifecycle. This is an internal capability,
not a new public endpoint or a runtime authorization mechanism.

## Standard checkout stays standard
`process_order(order_id, customer_id, amount)` retains its signature and sequence:

1. Reject nonpositive amounts before database reads.
2. Resolve and validate the active customer.
3. Resolve and validate the PENDING order.
4. Delegate to `process_payment(customer.payment_token, amount)`.
5. Mark the order PAID, save, send its receipt, and return the order.

The inexpensive positive-amount guard appears at both entry points deliberately:
checkout must keep its early failure ordering, while payment-only callers must
not be allowed to send a nonpositive charge. Gateway execution and failure
translation have exactly one owner, `process_payment`.

## Internal usage
```python
# Caller has already authorized/verified this enterprise account and obtained
# its gateway payment token. No customer-order record is required here.
result = order_service.process_payment(enterprise_payment_token, amount)
```
The result is the gateway's successful result object, not an order. A gateway
rejection raises `Exception("Payment failed: " + payment_result.error)`; an
amount <= 0 raises `ValueError("Amount must be positive")`.

## Why this shape
The existing method combines payment execution with customer-order orchestration.
Extracting the coherent payment operation enables the new callers without
weakening ordinary checkout or duplicating gateway/error logic. Keeping two
small methods in the existing class is sufficient for this one-file service;
new service classes, strategy hierarchies and configuration are unnecessary.

Avoid `skip_validation`, `skip_pending_check` or `send_receipt=False` switches:
they entangle unrelated policies, permit inconsistent combinations and blur
which workflow the caller requested. Do not create dummy PENDING orders or
inactive-customer exceptions just to reuse checkout.

## Boundaries and verification
No schema, constructor, dependency, gateway interface or amount type changes.
No retries, idempotency mechanism, scheduler, batch runner or recovery policy is
introduced. Payment succeeds before persistence/notification as before; this
change does not make those existing operations transactional.

Tests must verify payment-only success/rejection/exception propagation and
nonpositive amounts with zero database/notification interactions. Checkout
regressions must verify prerequisite failures, one charge, PAID/save/receipt
ordering, unchanged returned order, and no completion on payment failure.
