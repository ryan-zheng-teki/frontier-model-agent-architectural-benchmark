# Design

Design rationale for `order_service.py`. Later changes to this project should
read and follow the rules here.

## Payment Entry Points

`OrderService` is the one owner of "charge an order and record it". It has two
public entry points, one per kind of caller:

| Entry point | Callers | Checks | Notification |
| --- | --- | --- | --- |
| `process_order(order_id, customer_id, amount)` | Customer checkout | amount > 0; customer exists **and is active**; order exists **and is PENDING** | Receipt to the customer |
| `process_internal_enterprise_payment(order_id, customer_id, amount)` | Internal subscription billing jobs and admin batch tasks charging pre-verified enterprise accounts | amount > 0; customer exists; order exists | None |

Both entry points use the same private step, `_charge_and_mark_paid`. It charges
the customer's stored payment token through the payment gateway. A failed
charge raises `Exception("Payment failed: …")` and leaves the order unchanged.
A successful charge marks the order `PAID` and saves it.

### Why the internal path skips these checks

Internal callers validate accounts and score fraud before calling, and their
orders do not go through the customer `PENDING` lifecycle. The customer active
check, the `PENDING` check and the receipt therefore do not apply to them.

### Why the internal path keeps the other checks

The request named exactly three checks to skip. Everything else stays:

- **Amount > 0:** a zero or negative charge is never valid.
- **Customer exists:** its stored payment token is needed to charge.
- **Order exists:** the payment has to be recorded on it.
- **Same failure handling and `PAID` update:** both paths record payments the
  same way.

### Why a separate method and not a flag

A parameter such as `process_order(..., skip_checks=True)` would let any code
that can call checkout turn off the customer protections, sometimes just by
passing one more field through. A separately named method keeps
`process_order` exactly as it was. It also makes every use of the relaxed path
easy to find (`grep process_internal_enterprise_payment`) and easy to reject in
code review when it shows up in customer-facing code.

### Why one shared charge step

Copying the charge, failure handling and `PAID` update into a second method
would create two copies of the payment rules that could drift apart. One shared
private step keeps a single owner. The receipt stays outside that step, in
`process_order` only, so internal charges can never send one.

### Why not a separate service class

A separate `InternalBillingService` class would only forward to the same charge
logic. Either it would own nothing, or the charge rules would end up split
between two classes. With one small owner and no composition root in this
codebase, a method on `OrderService` is the proportionate choice. If internal
and customer code ever share a process where customer code can reach any
`OrderService` method, revisit this (see Known Risks).

## Rules For Future Changes

1. Do not add parameters that turn off checks or notifications on a payment
   entry point. Add a separately named entry point for a genuinely different
   kind of caller.
2. Charge-and-record logic lives only in `_charge_and_mark_paid`. Notifications
   and lifecycle checks stay in the entry points.
3. Customer-facing code calls `process_order` only.

## Known Risks (Accepted By The Request)

- **Duplicate charges on the internal path.** The `PENDING` check was also the
  only protection against charging an order twice. Without it, a retried or
  duplicated internal job charges the same order again. Upstream callers own
  retries and idempotency for now. Recommended follow-up: an idempotency key
  per billing cycle passed to the gateway, or a per-cycle charge record.
- **Inactive accounts can be charged on the internal path.** Upstream
  validation owns this, as the request states.
- **Caller restriction is by convention only.** Python cannot stop
  customer-facing code from calling the internal method. Recommended follow-up:
  expose the internal method only to internal job composition, or through a
  separate interface.

## Verification

Unit tests in `test_order_service.py` (stdlib `unittest`, Python 3.9) cover
both paths: unchanged customer behavior and exact error messages, internal
charges for inactive customers and non-`PENDING` orders, no notification on the
internal path, the kept checks, payment failure, and the unchanged
`process_order` signature. Run them from the project root with
`python3 -m unittest -v`.

Ticket record: `tickets/done/internal-enterprise-payment/` (requirements,
design spec, investigation notes, review, validation and delivery records).
