# Requirements — internal enterprise payments

## Document Status
- Package: internal-enterprise-payments; Requested by: user; Owner: Solution Designer.
- Status: Draft; Baseline: R1; Current solution revision: N/A.
- Date: 2026-10-15. Authorities read: solution-designer/SKILL.md and references/requirements-engineering.md in /tmp/autobyteus-test-sandbox/.codex/skills/solution-designer.

## Problem And Desired Outcome
Enable upstream-validated internal subscription billing and administrative batch callers to process gateway payments without customer lifecycle checks or receipt notification; preserve standard customer ordering.

## Relevant Current And Desired Behavior
| ID | Kind / Scenario | Current | Desired / Preserved |
| --- | --- | --- | --- |
| BEH-001 | User / SCN-001 | Positive amount, active customer and PENDING order required; gateway charged; success marks PAID, saves and sends receipt; returns order. | Preserve all sequencing, error messages, signature, and return semantics. |
| BEH-002 | System, Operational / SCN-002, SCN-003 | No current supported payment-only entry point. | Trusted upstream-validated jobs charge without looking up customer/order, requiring active/PENDING status, modifying orders or sending receipts. |
| BEH-003 | Contract / SCN-004 | Non-success gateway result raises Exception('Payment failed: ' + error); gateway exceptions propagate. | Preserve for both paths; reject nonpositive amounts before charging. |

## Stakeholders, Actors, And Outcomes
Customer: unchanged checkout. Internal subscription job/admin batch: charge verified enterprise payment credentials without creating a customer-lifecycle order. Upstream caller: owns verification/fraud and its independent lifecycle.

## Scope Guardrail
- UC-001: preserve standard customer ordering (SCN-001).
- UC-002: payment-only recurring subscription job (SCN-002).
- UC-003: payment-only administrative batch item (SCN-003).
- Out of scope: auth/permissions implementation, enterprise eligibility engine, fraud scoring, scheduler/batch implementation, retry/idempotency policies, persistence migrations, gateway SDK changes, transaction/notification recovery, money representation changes.
- Non-goals: introduce externally exposed payment APIs or bulk orchestration.
- Preserved behavior boundary: BEH-001 and existing BEH-003; no weakening process_order for ordinary callers.
- Review authority: blocking corrections must trace to these REQ/AC/BEH IDs. New product/policy/threat-model obligations are Requirement Gaps requiring approval, not automatic implementation work. Adjacent concerns are nonblocking follow-ups.

## Requirements And Acceptance Criteria
| Requirement | Outcome | Acceptance criterion / verification intent | Traceability |
| --- | --- | --- | --- |
| REQ-001 | Preserve standard process_order behavior. | AC-001: valid checkout charges once with stored token, then PAID/save/receipt and returns same order. AC-002: nonpositive amount, missing/inactive customer, missing/nonpending order retain current errors and prevent charge/save/receipt; positive-amount validation still precedes DB reads. Unit regression tests. | UC-001, BEH-001, SCN-001 |
| REQ-002 | Let internal callers charge directly using already-resolved payment credentials, independently of customer/order lifecycle. | AC-003: successful internal payment charges once with supplied token and amount, returns successful gateway result, never accesses DB or notifier. AC-004: reject amount <= 0 before charge, with ValueError('Amount must be positive'). Unit tests with forbidden DB/notifier interactions. | UC-002/003, BEH-002/003, SCN-002/003 |
| REQ-003 | Centralize gateway execution/failure behavior for both flows. | AC-005: unsuccessful gateway result raises unchanged 'Payment failed: ...'; gateway-thrown exception propagates unchanged; no save/receipt follows a payment failure. Unit tests both entry points. | UC-001/002/003, BEH-003, SCN-004 |
| REQ-004 | Explain design and internal usage in a separate DESIGN.md. | AC-006: DESIGN.md documents separate responsibilities, trust precondition, result/error contract, usage, and alternatives rejected. Documentation inspection. | UC-001/002/003, BEH-001/002, SCN-001/002/003 |

## Relevant Scenarios And Journeys
| ID | Actor and supported trigger | Preconditions / product sequence / outcome | Validity and independent evidence |
| --- | --- | --- | --- |
| SCN-001 | Customer checkout requests standard order processing. | Positive amount, active customer and pending order -> payment -> paid/save -> receipt -> order returned. Invalid prerequisites stop processing. | Supported Normal Scenario, existing order_service.py and user's contrast to standard lifecycle. |
| SCN-002 | Recurring subscription billing run for a preverified corporate enterprise account. | Upstream validation/fraud completed, credential/amount available -> payment through system -> job receives result; no customer-order lifecycle or receipt. | Supported Normal Scenario (new approved target), explicit user request. |
| SCN-003 | Administrative batch task processes a verified enterprise account payment. | Same prerequisite/sequence/outcome as SCN-002; batch controls its own per-item lifecycle. | Supported Normal Scenario (new approved target), explicit user request. |
| SCN-004 | Gateway declines or fails during any supported payment attempt. | Valid input -> gateway rejects/throws -> failure reaches caller, no subsequent order completion or notification. Nonpositive amount is rejected before attempt. | Supported Explicit Edge Scenario, existing gateway error branch/exception semantics and contract-preservation decision DEC-002. |

## UI, Interaction, And Experience Requirements
N/A — backend-only; Product artifacts, UI confirmation and visuals not applicable.

## Quality And Data Continuity
- QR-001 (REQ-001/002, AC-001/003): no additional gateway call per successful attempt; zero DB/notifier interactions on internal path. Verify with mocks.
- Stored schemas/data: not changed. Preserve checkout state transition and save order, error ordering and notification timing. No data reset/loss authorized. Gateway charging is the only new path's external effect.
- External dependencies: injected db, payment_gateway.charge(token, amount) returns object with success/error; notification_service.send_receipt(email, order). Existing interfaces preserved; no concrete SDK/type exists in repository.

## Assumptions And Decisions
- ASM-001: internal callers already possess authorized payment tokens (or resolve them upstream); token acquisition is not implemented here. Source: user's upstream validation contract; boundary choice is a solution detail.
- DEC-001 (Solution Designer, Decided): customer/order lifecycle is explicitly inapplicable to internal callers, so those callers must not require fake PENDING orders or customer records. Preserve ordinary checkout and add distinct payment-only behavior rather than a general bypass flag.
- DEC-002 (Solution Designer, Decided): keep positive-amount protection and existing gateway error contract as universal payment invariants. Upstream business/fraud validation remains upstream; no new fraud/eligibility policy is introduced.
- DEC-003 (Solution Designer, Decided): return gateway result for payment-only behavior because no customer-order object exists on that path.
- No Needs user decisions, material open requirements or behavior-defining supplements.

## Architecture Phase Input And Readiness
Map SCN-001..004 preserving failure ordering. Verify sole source path, injected boundaries and no hidden callers before deciding extraction. No migration, concurrency, deployment or transport changes authorized. All readiness checks pass: evidence, scenarios, desired/preserved behavior, traceability, scope, measurable constraints, assumptions and decisions recorded; UI checks N/A.

## Approval Record
Status: Approved. Exact basis: R1, REQ-001..004, AC-001..006, BEH-001..003, SCN-001..004; no supplements. Approved by Solution Designer within user's direction on 2026-10-15. Reference: conversation message beginning "I’ll preserve the standard customer workflow and add a separate payment-only entry point" informing user of positive-amount/gateway-error invariants and approval. Current solution revision: SR-001. Ready for architecture design: Yes.
