# Payment execution and order processing

`OrderService.process_payment(payment_token, amount)` is the entry point for
pre-verified corporate subscription jobs and administrative batch tasks. It
charges the supplied token through the existing gateway and returns the gateway
result on success. A declined payment raises the existing `Payment failed: ...`
exception; exceptions raised by the gateway propagate to the caller.

```python
# Account validation and fraud screening have already completed upstream.
payment_result = order_service.process_payment(account.payment_token, amount)
```

The payment operation has no dependency on a customer record or an order. It
does not check customer status, fetch or require a pending order, update order
state, or send a receipt. Internal callers own their billing records, lifecycle,
and any notifications. Accepting a payment token directly lets those callers
use their already-verified account data without creating a synthetic customer
order just to access the gateway.

`process_order` retains the customer workflow: validate the amount, require an
active customer and a pending order, execute the payment, save the order as
`PAID`, and send the receipt. It delegates payment execution to `process_payment`
so gateway calls and unsuccessful-payment handling have one implementation.
Its arguments, returned order, error messages, and validation order are preserved.

Both entry points reject non-positive amounts. The small guard remains at the
start of `process_order` so invalid amounts still fail before database access;
`process_payment` also checks it so direct callers retain that basic invariant.
This does not repeat account validation or fraud scoring.

A separate operation keeps the customer workflow explicit and avoids adding
flags that selectively disable its checks or notifications. This service has
no authentication or enterprise-account authorization infrastructure. The
calling application must restrict access to the payment entry point to trusted
internal callers and establish account eligibility upstream; possession of a
payment token alone does not establish authorization.

This change retains existing gateway and failure semantics. It adds no automatic
retries or idempotency mechanism; callers must use their billing system's
existing safeguards when scheduling or retrying payments.

## Verification

Run `python -m unittest discover -v`. Tests cover direct payments without any
database or notification calls, gateway failures and exceptions, non-positive
amounts, and the existing customer workflow's validation, state updates, receipt,
and failure behavior.
