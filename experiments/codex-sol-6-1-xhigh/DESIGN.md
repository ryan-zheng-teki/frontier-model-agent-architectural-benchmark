# Internal enterprise payment processing

`OrderService.process_internal_order(order_id, customer_id, amount)` is the entry
point for recurring billing jobs and administrative batch tasks processing
pre-verified corporate enterprise accounts. It charges the customer's stored
payment token, marks the order `PAID`, saves it, and returns the order.

This path does not inspect customer activity or order status and does not send a
customer receipt. Internal orders therefore do not need to enter the customer
`PENDING` lifecycle. The caller owns enterprise eligibility, authorization,
validation, and fraud scoring. This method is a trusted service API, not an
authorization boundary; it must not be exposed directly to customer-controlled
requests. The repository provides no enterprise-account or caller-identity model
with which to enforce those upstream responsibilities here.

A separate entry point makes the intended caller and behavior explicit without
adding bypass flags to customer checkout. Existing `process_order` callers retain
the positive-amount, active-customer, and pending-order checks and receipt behavior,
including the existing return value and payment-failure behavior.

Both paths use `_charge_and_mark_paid` for gateway execution and persistence, so a
gateway failure prevents the state update and any receipt. The internal path
retains the positive-amount invariant and checks that the customer and order
exist: a stored payment token and a record to update are still required. These
checks do not require customer activity or a particular order status.

The shared helper preserves the existing charge-then-save sequence. Idempotency,
retry handling, and recovery from a persistence failure after a successful charge
remain outside this change. Internal callers must avoid submitting the same
payment twice; this path intentionally has no order-status guard.

Run `python -m unittest discover -v` to verify customer checkout regression cases,
internal processing without activity/status fields, required input records, and
gateway failure behavior for both entry points.
