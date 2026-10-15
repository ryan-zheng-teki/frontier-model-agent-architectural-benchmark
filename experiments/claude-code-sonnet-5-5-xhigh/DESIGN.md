# Design: Internal payment path for enterprise billing jobs

## Requirement

Internal recurring subscription billing jobs and admin batch tasks must charge
pre-verified corporate enterprise accounts through the payment gateway
**without** these three steps of `process_order`:

1. the customer active-status check,
2. the order `PENDING` state check,
3. the customer receipt notification.

These callers do their own validation and fraud scoring upstream.

## Decision: a separate method, not a flag on `process_order`

I added `OrderService.process_internal_payment(order_id, customer_id, amount, *, initiated_by)`
and left `process_order` unchanged.

### Alternatives I rejected

| Option | Why not |
|---|---|
| `process_order(..., skip_checks=True)` or several `skip_*` flags | Any caller that can reach `process_order`, including customer-facing endpoints, could turn the safety checks off with one argument. Wrong flags are easy to pass by accident, and they're hard to spot in review or grep. A flag also mixes two different contracts in one method. |
| Subclass / separate `InternalBillingService` class | Cleaner isolation, but it either copies the dependency wiring or reaches into `OrderService` internals. With one method it isn't worth it yet. If more internal-only operations show up, moving `process_internal_payment` into its own service is a mechanical change. |
| Change the customer flow to accept other order states | That would weaken the customer path, which is what the checks are there to protect. |

### Why a separate method works

- **The customer path behaves exactly as before.** `process_order` has no new
  parameters and no new branches, so existing callers can't hit the bypass.
- **Exposure is explicit.** Customer-facing code has to call a method whose
  name says "internal", which makes misuse obvious in code review and easy to
  find with grep.
- **Each contract is separate.** Each method's docstring describes one set of
  guarantees.

## What the internal path still enforces, and why

Skipping the three named checks doesn't mean skipping all checks. I kept only
the ones the requirement didn't name and that protect the system itself rather
than the customer lifecycle:

| Check | Kept? | Rationale |
|---|---|---|
| `amount > 0` | Kept | Not named in the requirement. A zero or negative charge is never valid. It costs nothing, and it catches bugs in batch jobs. |
| Customer exists | Kept | We need the customer's `payment_token` to charge. Only the **active-status** check is skipped. |
| Customer `is_active` | **Skipped** | Per the requirement. Upstream callers own this decision. |
| Order exists | Kept | Every charge stays tied to a persisted order record, which keeps the audit trail. Only the **`PENDING` status** check is skipped. |
| Order `status == "PENDING"` | **Skipped** | Per the requirement. Internal orders don't follow that lifecycle. |
| Receipt notification | **Skipped** | Per the requirement. |
| Order marked `PAID` and saved | Kept | Keeps order state consistent with what was actually charged. |

## Accountability: `initiated_by`

Internal payments skip checks, so every call has to be traceable:

- `initiated_by` is a **required keyword-only** argument, for example
  `"subscription-billing-job"` or `"admin:jdoe"`. An empty value is rejected.
- Each attempt is logged at INFO with the caller, order, customer, amount, and
  the order's **prior status**. Failures are logged at WARNING. Logging the
  prior status matters because the `PENDING` guard is gone, so the log is now
  the only record of which state an order was charged from.

## Known risks and open questions

These are deliberate gaps that I didn't fill with guesses. They need an owner's
decision:

1. **Double charging.** Without the `PENDING` guard, calling the method twice
   for the same order charges twice. That may be intended for recurring
   billing that reuses an order ID, but it's dangerous for retried batch jobs.
   The fix is gateway-level idempotency keys, or a guard against re-charging
   orders that are already `PAID`. The gateway's `charge(token, amount)` API
   has no idempotency parameter today, so I didn't invent one. **Callers must
   handle idempotency until then.**
2. **Access control is by convention only.** Python can't stop another module
   from calling this method. The method must not be wired into any HTTP or
   customer-facing handler. If stronger enforcement is needed, options include
   a separate service/module boundary, a capability token passed in by trusted
   job runners, or a lint rule.
3. **"Corporate enterprise account" isn't verified here.** The requirement says
   these accounts are pre-verified upstream, and the current customer model has
   no account-type field I can rely on. If such a field exists, adding an
   `account_type == "enterprise"` assertion would be a cheap safeguard.
4. **Orders must exist.** If internal jobs charge without creating an order
   record first, the "order exists" check will reject them. I kept it for
   auditability, but it can be revisited if that doesn't fit how the jobs work.
5. **Non-atomic charge then save** (inherited from `process_order`). If
   `save_order` fails after a successful charge, the customer is charged but
   the order isn't marked `PAID`. This affects both paths and is outside this
   change's scope.

## Small incidental note

In `process_order`, `"Payment failed: " + payment_result.error` raises
`TypeError` if the gateway returns `error=None`. The new method uses
`str(...)` to avoid this. I didn't change `process_order`, so its behavior
stays identical, but it's worth a follow-up fix.
