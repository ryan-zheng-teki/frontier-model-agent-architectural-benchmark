# Requirements Document

## Document Status
- Package: internal-enterprise-payments; baseline SR-001; status Approved.
- Requested by: User, request to implement internal subscription/batch payments and DESIGN.md.
- Owner/approval: Solution Designer within the direction, 2026-10-15.
- Approval reference: conversation message beginning “The gateway charge is currently tied”; exact baseline is REQ-001–004 below, no behavior-defining supplements.
- Authorities read: solution-designer/references/requirements-engineering.md (2026-10-15).

## Problem And Desired Outcome
Pre-verified enterprise recurring billing and administrative batches need gateway payments independent of the customer pending-order lifecycle. The existing customer workflow must remain unchanged.

## Relevant Current And Desired Behavior / Scenarios
| IDs | Actor, trigger, goal and product sequence | Current → desired / preserved | Validity and evidence |
|---|---|---|---|
| BEH-001, SCN-001, UC-001 | Recurring billing job, scheduled enterprise invoice: upstream verification → charge → return payment outcome | No payment-only operation → charge without customer status/pending-order checks or receipt; no customer order mutation | Supported Normal Scenario, explicit user requirement |
| BEH-002, SCN-002, UC-002 | Administrator starts batch for pre-verified enterprise accounts: upstream validation → each payment → caller handles result | Same new payment-only capability; scheduling and batch loop owned upstream | Supported Normal Scenario, explicit user requirement |
| BEH-003, SCN-003, UC-003 | Customer order processing: positive amount → active customer → pending order → charge → paid/save → receipt → return order | Preserve existing outcomes and ordering, including early validation rejection and gateway failure stopping downstream effects | Supported Normal Scenario; order_service.py:7–29 |

Gateway rejection/exception is a supported alternate for all scenarios, evidenced by current explicit rejection handling and external gateway boundary. Nonpositive amount rejection preserves current guard; extending that minimal invariant to the new operation is a within-direction decision, not repetition of upstream fraud/account checks.

## Scope Guardrail
In scope: UC-001/002 payment-only capability; UC-003 shared charge reuse with unchanged observable behavior; tests; requested DESIGN.md rationale.
Out of scope: job scheduling/batch orchestration, new authentication framework or enterprise account model, fraud scoring, retries/idempotency, money representation overhaul, transaction recovery, new HTTP endpoint, schema changes.
Non-goals: deploy or process real payments.
Preserved boundary: BEH-003/REQ-002; no weakening of normal customer safeguards.
Review authority: corrections must cite approved REQ/AC/BEH IDs; new behavior or policy requires renewed approval; unrelated findings are nonblocking follow-ups.

## Requirements, Acceptance Criteria And Traceability
| Requirement | Observable acceptance criteria | Traceability |
|---|---|---|
| REQ-001 Internal callers can charge a supplied gateway payment token and positive amount without customer/order lookup, status checks, receipt, or customer order writes | AC-001: one gateway charge with exact token/amount; successful gateway result returned unchanged; no database/notification access required | UC-001/002, BEH-001/002, SCN-001/002 |
| REQ-002 Preserve normal process_order contract and sequencing | AC-002: successful active-customer/pending-order request charges once, marks PAID, saves once, sends receipt once and returns original order; invalid amount/customer/order keeps existing messages and stops before subsequent effects | UC-003, BEH-003, SCN-003 |
| REQ-003 Preserve shared charge failure semantics and minimal amount invariant | AC-003: nonpositive amounts raise ValueError('Amount must be positive') before gateway invocation; unsuccessful result raises Exception('Payment failed: ' + error); gateway exception propagates; customer path neither saves nor notifies after payment failure | All UC/BEH/SCN IDs |
| REQ-004 Document usage and rationale separately | AC-004: root DESIGN.md describes boundaries, internal usage, upstream trust assumptions, preserved behavior and alternatives rejected | All UC/BEH/SCN IDs |

## Decisions And Assumptions
DEC-001 (Decided, Solution Designer): preserve positive-amount guard because invalid charges are not requested; upstream validation/fraud ownership does not require removal of a cheap payment invariant.
DEC-002 (Decided, Solution Designer): internal operation does not update customer order state because these callers have no standard pending-order lifecycle. They own their billing records.
ASM-001: internal callers can supply a previously obtained payment token and enforce enterprise eligibility/authorization; explicitly established upstream trust, token parameter is a technical seam not new account policy. No callers or identity framework present to wire.
No Needs user decisions; security bypass for trusted callers is explicitly user-directed, not broadened to untrusted customer entrypoints.

## Quality, Data, Dependencies And Supplements
Compatibility: exact AC-002 sequencing/messages and existing constructor/signature preserved.
External gateway contract: charge(token, amount) returns object with success/error; only local code is available; no provider integration or live validation claimed.
Data: existing customer writes preserved; internal path has no DB writes; no data loss/reset authorized, no schema change. Storage implementation absent.
Product/UI, visual supplements: N/A — not applicable, backend-only request.
Supplement: root DESIGN.md (technical rationale only; REQ-004; to be authored).

## Architecture Phase Input And Readiness
Architecture must map SCN-001–003 and keep gateway execution reusable without customer lifecycle coupling. API shape and local extraction deferred to design; verify whole sole-file call path after approval.
Readiness: current behavior evidenced, desired/preserved behavior explicit, scope bounded, all requirements traceable/testable, scenarios supported, assumptions recorded. Approved basis ready for design: Yes. Blockers: None.
