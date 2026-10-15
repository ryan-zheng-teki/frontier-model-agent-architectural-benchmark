# Design: Trusted internal payment path

## Problem

Recurring subscription billing jobs and administrative batch tasks must charge
pre-verified corporate enterprise accounts through the payment gateway. They do
their own validation and fraud scoring upstream and their orders do not follow
the customer `PENDING -> PAID` lifecycle, so they must not run the customer
status check, the pending-order check, or the customer receipt that
`OrderService.process_order` performs.

## Decision

Add a separate entry point, `EnterpriseBillingService.charge_account(customer_id, amount)`,
in `order_service.py`. Leave `process_order` behaving exactly as before. The only
change to it is that the "charge, and raise if declined" step moves into a shared
private function, `_charge_or_raise`, which both paths call.

```
Customer path:  caller -> OrderService.process_order -> [validate, pending check] -> _charge_or_raise -> gateway -> [save order, receipt]
Internal path:  billing job -> EnterpriseBillingService.charge_account -> [amount > 0, token lookup] -> _charge_or_raise -> gateway
```

### What the internal path does and does not do

| Step | `process_order` | `charge_account` |
| --- | --- | --- |
| amount > 0 | yes | yes |
| customer exists (needed for payment token) | yes | yes |
| customer `is_active` | yes | **skipped** (requirement) |
| order exists and is `PENDING` | yes | **skipped** (requirement) |
| gateway charge, raise `Payment failed: ...` on decline | yes | yes (shared) |
| mark order `PAID` and save | yes | no, the order record is not read or written |
| customer receipt | yes | **skipped** (requirement) |
| returns | the order | the gateway result |

## Why not the obvious alternatives

**A `skip_validation=True` / `trusted=True` flag on `process_order`.** This is the
smallest diff, but it puts a "bypass the checks" switch on the method that
customer-facing code calls. One wrong call site, or one value derived from
request input, turns off the customer-active check and the pending-order check
for a real customer. It also leaves a method with several boolean-controlled
modes, which is hard to read and test. The requirement says these callers do not
follow the customer lifecycle, so they are a different use case and get their
own entry point.

**Separate class rather than a second method on `OrderService`.** The trusted
service takes only `db` and `payment_gateway`. It has no `notification_service`,
so it cannot send a receipt even by mistake. Dependency injection also gives a
real boundary: customer-facing code is wired with `OrderService`, and only
internal jobs are given `EnterpriseBillingService`. A second method on
`OrderService` would give every holder of that object the bypass.

**Copying the charge logic into the new method.** The decline handling is
payment policy that should stay identical on both paths, so it has one owner
(`_charge_or_raise`). The exception type and message are unchanged, so existing
callers of `process_order` see no difference.

**Having the caller pass a `payment_token` directly.** This would remove the
database read. It would also make every job responsible for obtaining and
handling raw payment tokens. Looking the token up by `customer_id` keeps token
handling in one place and matches how `process_order` already works.

## Decisions I made where the requirement was silent

1. **Keep the `amount > 0` check.** The requirement lists three checks to skip and
   this is not one of them. It is a cheap sanity check on money, not a customer
   or lifecycle check. Upstream fraud scoring does not obviously cover a zero or
   negative amount.
2. **Still look up the customer, but only for the payment token.** An unknown
   account raises `ValueError("Unknown customer account")` and nothing is
   charged. `is_active` is deliberately not read.
3. **Do not touch the order record.** The requirement says these orders do not
   follow the pending lifecycle, so there is no `PENDING -> PAID` transition to
   perform. The gateway result is returned so the caller can record the outcome
   in its own system. If the team later wants a `PAID` marker for these charges,
   that needs its own requirement, because the lifecycle for them is not defined.

## Risks to be aware of

- **Charging inactive customers is now possible by design.** The `is_active`
  check is skipped as requested. If an enterprise account is deactivated, for
  example for non-payment or a compliance hold, a job that does not check this
  upstream will still charge it.
- **No double-charge protection in this path.** In `process_order`, the pending
  check stops a second charge once an order is `PAID`. Here nothing stops a
  retried or duplicated job from charging twice. The gateway interface in this
  repository is `charge(token, amount)` with no idempotency key, so this service
  cannot add one. Callers must make retries safe until the gateway supports it.
- **Python cannot enforce "internal only".** The restriction is by wiring and
  convention. If it needs to be enforced, add an authorization check at the
  service-construction or API layer, outside this file.
- **No audit trail from this service.** There is no order reference and no
  logging here, so a charge is traceable only through the gateway's own records
  and the caller's logs.

## Suggested follow-ups (not done, out of scope)

- Add an idempotency key or reference to `payment_gateway.charge` and pass it
  from `charge_account`.
- Decide whether enterprise charges need an audit record or log entry.
- Decide whether deactivated enterprise accounts should be blocked by the
  calling jobs, or by a dedicated enterprise-account check owned by this service.

## Verification

Run everything with `python3 -B -m unittest discover -p "test_*.py"` (17 tests).

- `test_order_service.py` (9 tests). Four pin the existing `process_order`
  behavior: success, inactive customer, non-pending order and declined payment.
  Five cover the internal path: it charges an inactive customer without reading
  or writing orders, a decline raises, amounts of 0 or less are rejected before
  any lookup or charge, an unknown account is rejected without charging, and the
  service has no notification dependency.
- `test_enterprise_billing_boundary.py` (8 tests). It drives both services
  through their public methods against stateful fakes that record an ordered
  call log. It covers each acceptance criterion, a mixed billing-job batch,
  customer and internal traffic sharing the same collaborators, and a 96-case
  differential that compares `process_order` with a reconstruction of its
  original logic (outcome, exception, call order, order state, receipts).
- A mutation probe of 9 deliberate regressions in `order_service.py` was caught
  by both test files. The probe was a one-off check and is not kept in the repo.

Not verified:

- Behavior against a real gateway or database. Both are fakes or mocks, because
  none exist in this repository. The gateway and db contracts used by the tests
  (`charge(token, amount)` returning an object with `success` and `error`;
  `get_customer`, `get_order`, `save_order`) are inferred from how
  `order_service.py` uses them and should be confirmed by the owner of the real
  implementations.
- The original `process_order` comparison uses a reconstruction of the old
  logic, not a version-control baseline, because the project is not a git repo.
- Not tested by design: caller authorization, double-charge or retry behavior,
  and `NaN` amounts. These are the accepted risks listed above.
