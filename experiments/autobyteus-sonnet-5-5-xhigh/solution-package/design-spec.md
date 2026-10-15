# Design Spec — enterprise-internal-billing

Authorities read: design-principles.md, architecture-design.md. Project DESIGN.md: none pre-existing (see investigation notes). Rationale narrative: /Users/normy/Desktop/claude-test/DESIGN.md.

## Design-health assessment
- Change posture: feature. Root cause classification: Boundary Or Ownership Issue avoided — the new use case has a different trust level than the customer path, so it gets its own owner instead of a flag. Also Duplicated Policy: charge+decline handling gets one owner. Refactor needed now: yes, minimal (extract `_charge_or_raise`).

## Spines
- S-1 (existing, UC customer) `caller -> OrderService.process_order -> validation/order state -> _charge_or_raise -> gateway -> save order -> notification`.
- S-2 (new, UC-001) `billing job/batch task -> EnterpriseBillingService.charge_account -> amount check + token lookup (db) -> _charge_or_raise -> gateway -> result to caller`.
- Owners: `OrderService` owns customer order lifecycle; `EnterpriseBillingService` owns trusted internal charge sequencing; `_charge_or_raise` owns charge-and-fail policy.

## Rejected alternatives
Boolean bypass flag on `process_order`; second method on `OrderService`; duplicated charge code; caller-supplied payment token. Reasons in DESIGN.md.

## Change inventory (Change Scope)
- Modify `order_service.py`: add `_charge_or_raise`; `process_order` uses it (behavior unchanged); add `EnterpriseBillingService`.
- Add `test_order_service.py`; add `DESIGN.md`.
- Removal plan: nothing removed; the two inline decline lines in `process_order` are replaced by the helper. No dead code found in the touched file.
- Left alone: gateway, db, notification interfaces; order lifecycle; authorization.
- Follow-ups: gateway idempotency key/reference; audit logging; deactivated-account policy; enforce internal-only access at the wiring/API layer.
- Persisted data: Not Affected. Dependency rule: customer-facing code depends on `OrderService` only; internal jobs on `EnterpriseBillingService` only.

## Requirement mapping
REQ-001..003 -> `charge_account` omits those steps (no `is_active`, no `get_order`, no notifier). REQ-004 -> `_charge_or_raise`. REQ-005 -> `process_order` unchanged apart from the helper call. REQ-006/007 -> first two steps of `charge_account`.

## Classification
- task_size: Small (one file, ~35 lines).
- architectural_risk: High. Evidence: it adds a new payment entry point that bypasses customer-status and order-state controls (material security / contract behavior), and removes the double-charge guard on that path. Escalation trigger: any change to the gateway contract, or exposing the service to customer-facing code.
