# Design Rationale: Claude Code (Sonnet 5.5, Thinking: xhigh)

## Implementation Summary
Added a separate method, `process_internal_payment`, for internal billing jobs and left `process_order` as the strict customer path. All 16 unit tests pass.

## Design Decisions

1. **No "skip checks" option on `process_order`:**
   A flag like `skip_checks=True` would let any customer-facing caller turn off the active-customer and order-state checks with one argument. A separately named method is easy to find with a search and easy to review.

2. **Shared payment steps, separate rules:**
   The two methods share helpers that validate the amount, charge the gateway, and mark the order PAID. Each method decides for itself which checks apply.

3. **Callers must identify themselves:**
   The new method requires an `InternalBillingContext` with a caller type (subscription billing or admin batch) and a non-blank `job_id`. Every attempt, success, and failure is logged with the caller, job, order, account, and amount.
   *(Note from agent: Any code in the same process can create this object, so it is not authentication. Real protection means never exposing this method through a customer-facing route.)*

4. **Only the three named checks are skipped:**
   The method still checks:
   - That the amount is valid.
   - That the account exists, since its payment token is needed to charge.
   - That the order exists.
   - That the order is not already PAID, so a retried or re-run job cannot charge the same order twice.

5. **Shared Helper Modifications affecting `process_order`:**
   - NaN, infinite, and non-numeric amounts are now rejected.
   - A failed payment raises `PaymentFailedError`, a subclass of `Exception`, preserving error message conventions.
   - Gateway charge failures with no error text now report `"Payment failed: None"` rather than crashing with `TypeError`.
