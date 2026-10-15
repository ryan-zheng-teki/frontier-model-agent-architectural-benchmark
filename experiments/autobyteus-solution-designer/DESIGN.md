# Design Spec: Internal Enterprise Billing Service

**Revision:** SR-002  
**Designer:** AutoByteus Solution Designer  
**Status:** Approved & Ready  

---

## 1. Executive Summary & Design Decision

- **Core Decision:** Do NOT modify `OrderService`. Do not add boolean flags or ad-hoc bypass methods to `OrderService`.
- **Structural Solution:** Introduce an independent sibling service, `InternalBillingService`, dedicated exclusively to internal enterprise account charges.
- **Composition Root Isolation:** `InternalBillingService` is wired exclusively into internal batch / worker composition roots (`db`, `payment_gateway`). It has no dependency on `notification_service`, performs no order queries or state updates, and cannot be reached by customer-facing checkout routes.

---

## 2. Comparison Matrix

| Topic | AutoByteus Solution Designer | Frontier LLM / Agent Approach (Sonnet / Claude Code) |
| :--- | :--- | :--- |
| **Class Modified** | None (`order_service.py` is untouched) | `OrderService` (bloated with batch logic) |
| **New Service** | `InternalBillingService` | None (everything crammed into `OrderService`) |
| **Customer Regression Risk** | **Zero** (no code changes to customer paths) | **High** (shared helpers & bypass methods exposed) |
| **Dependencies Required** | Only `db`, `payment_gateway` | Forced to accept `notification_service` |
| **Order Lifecycle** | Ignored (batch billing has no orders) | Forced dummy order checks (Claude Code) |
| **Security Boundary** | Enforced by wiring at composition root | Unenforceable (leaked to all `OrderService` callers) |

---

## 3. Backward Compatibility Rejection Log

| Candidate Mechanism | Why Considered | Rejection Rationale |
| :--- | :--- | :--- |
| **Flags on `process_order` (`skip_validation=True`)** | Minimal diff size | **REJECTED:** Violates SRP, turns security invariants into opt-outs, causes codebase bloat. |
| **Shared bypass method on `OrderService` (`process_internal_payment`)** | Reuses `_charge` helper | **REJECTED:** Two separate domain lifecycles. Leaks bypass method to customer-facing wiring. |

---

## 4. Verification & Testing Strategy

- `OrderService` unit test suite runs completely unmodified, guaranteeing zero regression.
- `InternalBillingService` tests verify:
  1. Amount validity and finite checks.
  2. Account payment token resolution.
  3. Gateway invocation and error handling (`PaymentFailedError`).
  4. Audit logging of all outcomes (`REJECTED`, `DECLINED`, `CHARGED`).
  5. Assert that no order methods (`get_order`, `save_order`) and no notification methods are ever called.
