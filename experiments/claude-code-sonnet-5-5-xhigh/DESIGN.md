# Design: Internal payment path for pre-verified enterprise accounts

## Requirement
Internal recurring-billing jobs and admin batch tasks must charge pre-verified
enterprise accounts through the payment gateway without the customer status
check, the order-PENDING check, or the customer receipt in `process_order`.

## Decision
Add a separate method, `OrderService.process_internal_payment(reference_id,
customer_id, amount, caller)`. `process_order` is unchanged.

### Why a new method, not a `skip_checks=True` flag on `process_order`
- A bypass flag on the customer-facing path means one wrong argument, or one
  request-handler bug passing user input through, disables the safeguards for
  customers. A separate method keeps the standard path's guarantees intact.
- The internal flow is different in kind (no order lifecycle, no receipt), so a
  separate method is clearer than a function full of conditionals.
- Internal callers are easy to find and audit by searching for the method name.

## Behaviour
| Step | `process_order` | `process_internal_payment` |
|---|---|---|
| Amount > 0 | yes | yes (kept: cheap, and guards against bad batch data) |
| Customer lookup | yes, must be active | lookup only, to get the payment token; **no active check** |
| Order PENDING check | yes | **skipped** |
| Gateway charge | yes | yes; failure raises, as before |
| Order status update / save | yes | **not done**; the caller owns its own records |
| Customer receipt | yes | **skipped** |

Returns the gateway `payment_result` so the caller can record the transaction.

## Safeguards kept on purpose
- **Caller identity (`caller`) is required** and written to logs with the
  reference id, customer and amount on start, success and failure. Skipping
  validation is acceptable only if there is an audit trail of who did it.
- **Positive amount** and **customer existence** are still enforced; the
  charge cannot happen without a payment token.

## Assumptions and risks
- Upstream callers really do validate and fraud-score. This method trusts them
  and does not re-verify that the account is an enterprise account (the schema
  has no such field that I could see). If one is added, check it here.
- Access control is by convention and docstring only. The method is public on
  the service; it must not be wired to customer-facing routes. Stronger
  options if needed: move it to a separate `InternalBillingService`, or have it
  check a service-identity/allow-list.
- **No idempotency.** Recurring jobs that retry can double-charge. `reference_id`
  is logged but not passed to the gateway because `charge` takes no idempotency
  key today. Recommended follow-up: add one to the gateway call.
- Order state is not touched. If internal orders need a status update, add that
  explicitly rather than reusing the customer lifecycle.
