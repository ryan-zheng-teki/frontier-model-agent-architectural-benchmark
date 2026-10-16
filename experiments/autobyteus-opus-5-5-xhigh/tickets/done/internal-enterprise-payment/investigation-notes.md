# Investigation Notes

## Investigation Meta

- Package identifier: `internal-enterprise-payment`
- Request / ticket: the user's direct request in the Solution Designer conversation (2026-10-16): let internal billing jobs and admin batch tasks charge pre-verified enterprise accounts without the customer status check, the order pending check and the receipt notification in `process_order`; record the design rationale in a separate `DESIGN.md`.
- Workspace root: `/Users/normy/Desktop/claude-test`
- Repository mode: `Non-Git` (`git rev-parse` → "fatal: not a git repository")
- Task worktree / branch: N/A (non-git). Ticket artifacts live in `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/`.
- Resolved base remote / branch / revision: N/A (non-git)
- Finalization target remote / branch: N/A (non-git); the deliverable is the edited `order_service.py` and a new `DESIGN.md` in the workspace root
- Bootstrap result: Pass
- Bootstrap blocker: None
- Current solution revision ID: `SR-002`
- Authorities read (requirements reading gate; file and date): `references/requirements-engineering.md` (2026-10-16, opened in full by path)
- Authorities read (design reading gate; file and date): `references/architecture-design.md` and `references/design-principles.md` (2026-10-16, each opened in full by path); `references/design-examples.md` sections used (2026-10-16): Contents, Example 1, Example 10, Example 11, Common Bad-Practice Patterns, How To Use These Examples; project `DESIGN.md`: none existed before this ticket (`test -e DESIGN.md` → "no DESIGN.md"), so existing code conventions apply
- Investigation status: Complete for requirements and architecture

## Initial Request And Clarifications

- Original request: "Internal recurring subscription billing jobs and administrative batch tasks need to process payments for pre-verified corporate enterprise accounts. These internal callers already handle their own validation and fraud scoring upstream, and their orders do not follow the standard customer pending-order lifecycle. They need to process payments through our payment gateway via this system without running the customer status check, order pending check, or customer receipt notification in `process_order`." Plus: "Please implement this requirement, and document your design rationale in a separate `DESIGN.md` file."
- Clarifications received: None about the feature. A process detour about the skill's reading gates (resolved by PR #52 in `autobyteus-agents`) did not change the request.
- User-supplied facts and constraints: callers are internal (subscription billing jobs, admin batch tasks); accounts are pre-verified corporate enterprise accounts; callers do validation and fraud scoring upstream; their orders are not in the PENDING lifecycle; exactly three steps are to be skipped.
- Initial ambiguity: what else in `process_order` applies to the internal path (amount check, customer/order existence, PAID update, payment-failure handling); how the internal path is selected and kept away from customer callers; what protects against charging the same order twice once the pending check is gone.

## Product And Domain Understanding

- Product area: order payment processing (`OrderService`).
- Affected actors or systems: customer order checkout (existing caller of `process_order`, not in this workspace); internal recurring subscription billing jobs and admin batch tasks (new callers); payment gateway; notification service; order/customer store (`db`).
- Existing user or operational purpose: charge a customer's stored payment token for a PENDING order, mark the order PAID and email a receipt.
- Relevant terminology: "status check" = `customer.is_active`; "pending check" = `order.status == "PENDING"`; "receipt notification" = `notification_service.send_receipt`.

## Source Log

| Date | Source Type | Exact Source / Command / Query | Why Consulted | Relevant Finding | Follow-Up |
| --- | --- | --- | --- | --- | --- |
| 2026-10-16 | Code | `/Users/normy/Desktop/claude-test/order_service.py` (30 lines) | Only production code | One class, one method `process_order`; steps 1–4 below | None |
| 2026-10-16 | Command | `grep -rn "process_order\|OrderService" --include=*.py .` | Find callers/tests | Only the definition; no callers or tests in the workspace | Callers live outside this workspace (unknown U-001) |
| 2026-10-16 | Command | `git rev-parse --is-inside-work-tree` | Repository mode | Not a git repository | Non-git bootstrap |
| 2026-10-16 | Command | `test -e DESIGN.md`; `ls -la` | Project design authority | No `DESIGN.md`; only `order_service.py`, `.claude/`, `agent-feedback/` | The user asked for a new `DESIGN.md` |
| 2026-10-16 | Command | `python3 --version` | Runtime | Python 3.9.6 | Implementation must stay 3.9-compatible (no `match`, no `X \| Y` type unions at runtime) |
| 2026-10-16 | User | Request text above | Intended behavior | Three named skips; internal-only callers; upstream validation | — |

## Relevant Existing Behavior And Supported Product Paths

| Behavior ID | Kind | Supported Trigger Or Governing Contract | Current Supported Product Behavior Path / Lifecycle | Current Outcome / Invariants | Evidence | Confidence / Unknown |
| --- | --- | --- | --- | --- | --- | --- |
| BEH-001 | User | Customer checkout calls `process_order(order_id, customer_id, amount)` | amount > 0 → customer exists and active → order exists and PENDING → charge `customer.payment_token` → order PAID, saved → receipt to `customer.email` | Rejects non-positive amount, missing/inactive customer, missing/non-PENDING order (all `ValueError`), each before any charge; a failed charge raises `Exception("Payment failed: …")` and leaves the order unsaved and no receipt; the PENDING check also stops a second charge on an already-PAID order | `order_service.py:7-29` | High |
| BEH-002 | System / Operational | Internal subscription billing jobs and admin batch tasks charging pre-verified enterprise accounts | No current supported behavior. Today such callers can only use `process_order`, which rejects inactive customers and non-PENDING orders and always emails a receipt | — | Request; `order_service.py` | Proposed target trigger: a distinct internal invocation (see requirements) |

## Relevant Codebase And Technical Facts

| Path / Component / Contract | Current Responsibility Or Behavior | Requirement Implication | Architecture Question / Design Implication |
| --- | --- | --- | --- |
| `order_service.py:9-10` amount check | Rejects `amount <= 0` | Not among the three named skips; a non-positive charge is never valid | Share between both paths |
| `order_service.py:11-13` customer lookup + `is_active` | Combined `not customer or not customer.is_active` | Only the status part is to be skipped; the customer is still needed for `payment_token` | Split existence from status |
| `order_service.py:16-18` order lookup + PENDING | Combined `not order or order.status != "PENDING"` | Only the PENDING part is to be skipped; the order is still needed to record PAID | Split existence from lifecycle |
| `order_service.py:21-23` charge | `payment_gateway.charge(token, amount)`; on failure raises `Exception("Payment failed: " + error)` | Same gateway, same failure semantics wanted ("through our payment gateway via this system") | Share |
| `order_service.py:26-27` PAID + save | Sets `status = "PAID"`, `db.save_order` | Not among the skips; the payment must still be recorded on the order | Share |
| `order_service.py:28` receipt | `send_receipt(customer.email, order)` | Skipped for internal path | Customer-path only |
| Gateway contract | `charge(token, amount)` → object with `.success`, `.error` | No idempotency key in the observed interface | Duplicate-charge protection cannot be added at the gateway call without a contract change (out of scope) |

## Structural And Payload Surface Inventory

### Payload Or Content Surfaces

- Files, records, documents, catalogs, fixtures, or generated payloads: Order and customer records through `db`; no schema change.
- Existing readers, writers, or contracts that consume them: `process_order` reads customer and order, writes order status.
- Evidence paths: `order_service.py`.

### Structural Surfaces

- Runtime modules, shared interfaces, routes, APIs, persistence boundaries, security/concurrency controls, deployment configuration, or ownership boundaries: one public method `OrderService.process_order`. No API layer, authentication or caller identity exists in this workspace.
- Existing structural surfaces that can support the approved behavior: `OrderService` already owns the charge-and-mark-PAID sequence and has all three collaborators.
- Evidence paths: `order_service.py`.

### Potential Structural Impacts To Investigate

- API or external-contract change: a new public method on `OrderService` (additive); `process_order` signature unchanged.
- Persistence schema or invariant change: none to schema. The invariant "only PENDING orders get charged" no longer holds for the internal path (by request).
- Security or privacy boundary change: Yes. A path that skips the customer status check and the order lifecycle check, so the double-charge guard, is a weaker path. Who may reach it is a security boundary.
- Concurrency or lifecycle change: the internal path does not take part in the PENDING → PAID lifecycle precondition.
- Deployment, migration, ownership-boundary, architectural-pattern, or structural-refactoring change: None.
- Confirmed absent, present, or unknown: callers outside the workspace are unknown (U-001).

## Runtime, Probe, Or Reproduction Findings

| Method / Command | Scenario | Observation | Requirement Implication | Artifact / Evidence Path |
| --- | --- | --- | --- | --- |
| N/A | No runtime or tests exist in the workspace | — | Verification needs new unit tests with test doubles | — |

## Stakeholder And User Evidence

| Source / Actor | Need, Problem, Or Constraint | Evidence Strength | Requirement Implication | Open Question |
| --- | --- | --- | --- | --- |
| User (request) | Internal jobs must charge enterprise accounts without the three checks | Explicit | BEH-002 | None |
| User (request) | Upstream owns validation and fraud scoring | Explicit statement | This service does not re-check account type or fraud | None |

## External Contracts, Standards, And Dependencies

| Contract / Dependency | Version / Authority | Relevant Behavior Or Constraint | Evidence | Unknown / Risk |
| --- | --- | --- | --- | --- |
| `payment_gateway.charge` | Observed usage only | `(token, amount)` → `.success`, `.error` | `order_service.py:21-23` | No idempotency key; R-001 |
| `db.get_customer/get_order/save_order` | Observed usage only | Return `None` when missing (inferred from `not customer` / `not order`) | `order_service.py:11,16,27` | Low |
| `notification_service.send_receipt` | Observed usage only | `(email, order)` | `order_service.py:28` | None |

## Persisted Data And State Facts

- Affected stored or external subject: order `status` field (written to `"PAID"`, as today).
- Location and representative shape: via `db`; shape unchanged.
- Approximate volume: unknown; not material (no transformation).
- Current readers and writers: `process_order`.
- Current unknown/extra-field behavior: N/A.
- Required semantics or data that must be preserved: existing orders and statuses untouched.
- Acceptable loss, reset, rebuild, or regeneration: none needed.
- Privacy, retention, compliance, downtime, or operational constraints: none identified.
- Remaining evidence gap: None material.

## Product Design Request Context

- Product Design request in the current input: `Not stated`
- Other fields: N/A — not applicable (backend-only change; no UI).

## Product Design Findings

N/A — not applicable.

## Supplemental Artifact Inventory

| Artifact Path | Owner | Purpose | Scope | Related Requirement / AC IDs | Status | Approval Applicability / State |
| --- | --- | --- | --- | --- | --- | --- |
| `/Users/normy/Desktop/claude-test/DESIGN.md` | Solution Designer | User-requested design rationale for the project; also the project design document later tasks read | Whole feature | All | Current | Not behavior-defining; follows `design-spec.md` |
| `/Users/normy/Desktop/claude-test/agent-feedback/solution-designer-skipped-design-principles.md` | Solution Designer | Process feedback (skill gate), not part of this feature | None | None | Closed | Not applicable |

## Assumptions, Unknowns, And Risks

| ID | Type | Description | Why It Matters | Resolution / Owner | Status |
| --- | --- | --- | --- | --- | --- |
| U-001 | Unknown | Who calls `OrderService` outside this workspace, and whether customer-facing code could reach any method on it generically (e.g. dynamic dispatch by method name) | Decides how strongly the internal path must be separated from customer callers | Design separates by distinct method; follow-up F-002 for the deployment boundary | Open (follow-up) |
| R-001 | Risk | With the PENDING check skipped (as requested), a retried or duplicated internal call charges the same order again | Duplicate charges cost money and customer trust | Upstream callers own retry/idempotency (DEC-003); follow-up F-001 | Accepted by request; follow-up |
| R-002 | Risk | An inactive/closed account can be charged on the internal path | Charging a closed account | Upstream validation owns this per request (DEC-004) | Accepted by request |
| R-003 | Risk | A generic "skip checks" flag on `process_order` would let any customer-path caller turn off the checks | Security: fraud/abuse | Requirement REQ-005; design uses a separate method | Mitigated by design |

## Architecture Investigation Findings

- Entry point: `OrderService.process_order` (`order_service.py:7`) is the only entry point and the only owner of the charge sequence. No other module, test or caller exists in the workspace (grep above).
- Execution spine today: caller → `process_order` → `db.get_customer` → `db.get_order` → `payment_gateway.charge` → `db.save_order` → `notification_service.send_receipt`.
- Ownership: `OrderService` owns validation, the order state transition and the notification. The gateway, store and notifier are injected collaborators.
- Coupling: the two combined conditions (`not customer or not customer.is_active`, `not order or order.status != "PENDING"`) mix "the record is required to proceed" with "customer-lifecycle policy". The new path needs the first half without the second, so the conditions must be split. This is the only structural pressure.
- Transition constraints: none (no persisted-data change, no deployment).
- Duplication risk: copying lines 20–27 into a second method would create two copies of the charge-and-record policy that could drift (e.g. a future change to failure handling made in one only).
- Unresolved technical questions: U-001 only.

## Requirement Implications

- The request names exactly three skips; everything else in `process_order` stays in force on the internal path (DEC-001, DEC-002).
- The request says the callers are internal; the customer path must not gain a way to switch the checks off (REQ-005).
- No customer-facing behavior changes (REQ-001).

## Notes For Architecture Design

- Approved scenarios to realize: SCN-001 (customer checkout, unchanged), SCN-002 (internal enterprise charge).
- Verified constraints: Python 3.9; no existing tests; collaborators injected, so test doubles are easy.
- Questions for design: shape of the internal entry point; how to share amount check, lookups and charge-and-record without a flag; how to keep exact error messages of the customer path.
