# Investigation Notes — enterprise-internal-billing

Authorities read: requirements-engineering.md, architecture-design.md, design-principles.md. Project DESIGN.md: none existed before this task (the root `DESIGN.md` was created by this task as the user-requested rationale document).

## Workspace / bootstrap
- Workspace: /Users/normy/Desktop/claude-test (not a git repository; no worktree/branch/base/finalization target applicable; edits made in place).
- Prior blocker reports: none.

## Evidence
- E-1 `order_service.py` (30 lines originally): single class `OrderService(db, payment_gateway, notification_service)`, one method `process_order`: amount>0 -> `db.get_customer` + `is_active` -> `db.get_order` + status PENDING -> `gateway.charge(customer.payment_token, amount)` -> raise `Exception("Payment failed: ...")` on failure -> set PAID, `db.save_order` -> `notification_service.send_receipt(customer.email, order)` -> return order.
- E-2 Directory contained only `order_service.py` and `.claude/`: no callers, tests, gateway/db/notifier implementations, configs. Callers of `process_order` are unknown (checked by listing the directory).
- E-3 Gateway contract visible only through usage: `charge(token, amount)` returns object with `.success`, `.error`. No idempotency key or reference parameter is visible.
- E-4 Verification: `python3 -B -m unittest -v test_order_service` -> 9 tests OK (mocked collaborators).

## Unknowns
- U-1 Real gateway/db behavior and whether the gateway dedupes. U-2 Who the internal callers are and how they are authenticated. U-3 Whether enterprise orders exist as order records at all. U-4 Persisted data: none touched (Not Affected).

## Supplement inventory
- `/Users/normy/Desktop/claude-test/DESIGN.md` — user-requested design rationale; owner Solution Designer; non-normative summary of design-spec; no approval applicability.
- `/Users/normy/Desktop/claude-test/test_order_service.py` — executable checks for AC-001..AC-007.
