# Requirements Document

## Document Status

- Status: `Approved`
- Current solution revision ID: `SR-001`
- Package identifier: `internal-enterprise-payment`
- Request / ticket: the user's direct request in the Solution Designer conversation (2026-10-16), quoted in `investigation-notes.md`
- Requested by: the user (direct request)
- Requirements owner: Solution Designer (`/solution_designer`)
- Date: 2026-10-16
- Approved by and reference: `Solution Designer within the direction (user informed)`; reference: the Solution Designer message to the user on 2026-10-16 that summarizes these decisions (SR-001)
- Exact approved requirements baseline / solution revision: this document at `SR-001`
- Behavior-defining supplements and their approved versions: None

## Problem And Desired Outcome

- Problem: internal recurring subscription billing jobs and admin batch tasks must charge pre-verified corporate enterprise accounts. The only payment entry point, `process_order`, rejects inactive customers, rejects any order not in `PENDING`, and always emails a customer receipt. These callers validate and score fraud upstream, and their orders are not in the PENDING lifecycle.
- Affected actors or systems: internal billing jobs, admin batch tasks, customer checkout (must not change), payment gateway, notification service, order store.
- Desired outcome: internal callers can charge through the same gateway and have the payment recorded on the order, without the customer status check, the order pending check and the receipt. Customer checkout behaves exactly as before and gains no way to skip its checks.
- Observable definition of success: AC-001 to AC-008 pass.

## Relevant Current And Desired Behavior

| Behavior ID | Kind | Related Scenario IDs | Evidence-Backed Current Behavior | Desired Behavior | Intentionally Preserved Behavior | Investigation Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| BEH-001 | User | SCN-001 | `process_order` checks amount, customer exists and is active, order exists and is PENDING; charges; marks PAID; saves; emails receipt | No change | All of it: inputs, checks and their order, error types and messages, charge, PAID update, receipt | `order_service.py:7-29` |
| BEH-002 | System / Operational | SCN-002 | No current supported behavior. Proposed target trigger: an internal billing job or admin batch task explicitly asks for an internal enterprise charge | Charge the customer's payment token for the given order and amount and record the order as PAID, without the customer status check, the order pending check and the receipt | Amount must be positive; customer and order must exist; same gateway; same payment-failure behavior; order saved as PAID | Request; `order_service.py` |

## Stakeholders, Actors, And Outcomes

| Actor / Stakeholder | Goal Or Responsibility | Required Outcome | Important Constraint |
| --- | --- | --- | --- |
| Internal subscription billing job | Charge enterprise subscriptions each cycle | Payment charged and recorded; no customer receipt | Orders may be in any status; upstream owns validation, fraud scoring, retries |
| Admin batch task | Charge enterprise accounts in bulk | Same as above | Same as above |
| Customer (checkout) | Pay a pending order | Unchanged behavior and protections | Must not be able to reach the relaxed path through checkout inputs |
| Business / finance | Correct charging | No charge for non-positive amounts; failed charges not recorded as paid | Duplicate-charge protection on the internal path belongs to upstream callers (DEC-003) |

## Scope Guardrail (Mandatory)

### In-Scope Use Cases

| Use-Case ID | Use Case | Related Scenario IDs |
| --- | --- | --- |
| UC-001 | Internal enterprise charge: an internal billing job or admin batch task charges a pre-verified enterprise account for an order through this service | SCN-002 |
| UC-002 | Customer checkout payment stays unchanged (protected, not modified) | SCN-001 |

### Out Of Scope

- Authentication or authorization of internal callers at a network or deployment boundary (no such layer exists in this workspace; follow-up F-002).
- Idempotency keys or duplicate-charge detection for internal callers (gateway contract change; upstream owns it per the request; follow-up F-001).
- Checking that an account is an enterprise account or has passed fraud scoring (upstream owns it per the request).
- Invoices, statements or any other notification for internal charges.
- Audit logging infrastructure.
- Any change to the customer path's checks, messages or receipt.

### Non-Goals

- Making the internal path safe against misuse by its own internal callers (they are trusted per the request).
- A general "skip any check" configuration mechanism.

### Preserved Behavior Boundary

- BEH-001 in full; REQ-001; AC-001, AC-002.
- Cross-cutting invariant: no input of `process_order` can switch off any of its checks or its receipt (REQ-005).

### Review Authority

- Every blocking `Design Impact` or implementation-correction finding must cite an approved requirement, acceptance criterion, or preserved-behavior ID that it protects.
- A finding that would introduce new product behavior, policy, threat model, migration obligation, compatibility promise, or operational contract is a `Requirement Gap`; it requires explicit user approval before becoming authoritative.
- An adjacent concern outside the approved boundary may be recorded as a non-blocking risk, recommendation, or follow-up. It is not a required design correction.
- A downstream reviewer comment does not amend this requirements basis. The Solution Designer must update the canonical requirements and obtain renewed user approval before a scope-changing proposal can govern design or implementation.

## Requirements

| Requirement ID | Requirement | Related Behavior IDs | Priority / Criticality | Rationale | Source / Decision Reference |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Customer checkout payment (`process_order`) keeps its exact current behavior: same parameters, same checks in the same order, same error types and messages, same charge, PAID update and receipt. | BEH-001 | Critical | Customer protections must not weaken | Request scope; DEC-005 |
| REQ-002 | The service offers a distinct internal enterprise charge that charges the customer's stored payment token for the given order and amount through the existing payment gateway, without checking customer active status, without requiring the order to be PENDING, and without sending a customer receipt or any other notification. | BEH-002 | Critical | The request | Request |
| REQ-003 | The internal enterprise charge still rejects, before any charge: a non-positive amount; a customer that does not exist; an order that does not exist. Each rejection is a `ValueError` with a message that names the cause. | BEH-002 | High | These are not among the three named skips; the customer is needed for its payment token and the order to record the payment; a non-positive charge is never valid | DEC-001 |
| REQ-004 | On a successful internal charge the order is marked PAID and saved. On a failed charge the same payment-failure error as the customer path is raised, and the order is not saved and stays unchanged in status. | BEH-002 | High | The payment must be recorded the same way on both paths; not among the named skips | DEC-002 |
| REQ-005 | The internal enterprise charge is reached only by explicitly calling it. No parameter, flag or value of the customer checkout path can turn its checks or receipt off. | BEH-001, BEH-002 | Critical | Security: a skip switch on the customer path could be reached by customer-facing code | DEC-005 |

## Acceptance Criteria

| Acceptance-Criteria ID | Related Requirement IDs | Related Behavior / Scenario IDs | Preconditions / Trigger | Observable Expected Outcome | Important Alternate Or Failure Outcome | Verification Intent |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001 | REQ-001 | BEH-001 / SCN-001 | Active customer, PENDING order, positive amount, gateway succeeds; `process_order` called | Gateway charged once with customer's token and amount; order PAID and saved; receipt sent to customer email; order returned | — | Unit test with test doubles |
| AC-002 | REQ-001 | BEH-001 / SCN-001 | `process_order` with: amount ≤ 0; missing customer; inactive customer; missing order; non-PENDING order; gateway failure | Same errors and messages as today (`"Amount must be positive"`, `"Invalid or inactive customer"`, `"Order is not in pending state"`, `"Payment failed: <error>"`); no charge for the first five; no save and no receipt in all six | — | Unit tests |
| AC-003 | REQ-002, REQ-004 | BEH-002 / SCN-002 | Inactive customer, order in status other than PENDING (e.g. `"PAID"` or `"ACTIVE"`), positive amount, gateway succeeds; internal enterprise charge called | Gateway charged once with customer's token and amount; order PAID and saved; order returned | — | Unit test |
| AC-004 | REQ-002 | BEH-002 / SCN-002 | Any successful or failed internal enterprise charge | Notification service is never called | — | Unit test |
| AC-005 | REQ-003 | BEH-002 / SCN-002 | Internal enterprise charge with amount ≤ 0 | `ValueError("Amount must be positive")`; no charge, no save | — | Unit test |
| AC-006 | REQ-003 | BEH-002 / SCN-002 | Internal enterprise charge with a missing customer; separately, a missing order | `ValueError` naming the missing customer / missing order; no charge, no save | — | Unit tests |
| AC-007 | REQ-004 | BEH-002 / SCN-002 | Internal enterprise charge; gateway fails | `Exception("Payment failed: <error>")`; order not saved, status unchanged; no notification | — | Unit test |
| AC-008 | REQ-005 | BEH-001, BEH-002 | Inspect `process_order` signature | Signature is still `(order_id, customer_id, amount)`; no extra parameter that relaxes checks | — | Unit test on the signature plus code review |

## Relevant Scenarios And Journeys

| Scenario ID | Kind | Actor / Initiator / Governing Contract | Coherent Goal Or Governing Event | Supported Trigger / Entry Surface | Starting Condition | Product-Level Steps Or Event Sequence | Expected Outcome | Supported Alternate / Error Behavior | Scenario Validity | Independent Evidence / Decision Reference | Related Requirement / AC IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SCN-001 | User | Customer (checkout) | Pay a pending order | Checkout → `process_order` | Customer exists; order PENDING | Validate → charge → mark PAID → receipt | Order PAID, receipt sent | Rejections and payment failure as today | Supported Normal Scenario | `order_service.py` | REQ-001, REQ-005; AC-001, AC-002, AC-008 |
| SCN-002 | System / Operational | Internal subscription billing job or admin batch task | Charge a pre-verified enterprise account for an order | The internal enterprise charge (distinct from checkout) | Caller has validated and fraud-scored upstream; customer and order exist; order in any status | Validate amount, customer and order exist → charge → mark PAID | Order PAID; no notification | Non-positive amount, missing customer or order rejected; payment failure raised, order unchanged | Supported Normal Scenario | User request (2026-10-16) | REQ-002–REQ-005; AC-003–AC-008 |
| SCN-003 | User | Customer-facing code | Use the internal path from checkout to skip checks | — | — | — | Must not be possible through `process_order` inputs | — | Technically Possible but Unsupported/Contrived (recorded to keep it out of scope as a supported path) | REQ-005 | AC-008 |

## UI, Interaction, And Experience Requirements

- Applicable: `No`
- All Product design fields: N/A — not applicable (backend-only change).

## Quality And Non-Functional Requirements

| Quality ID | Related Requirement / AC IDs | Area | Measurable Requirement Or Constraint | Conditions / Scope | Verification Intent |
| --- | --- | --- | --- | --- | --- |
| QR-001 | REQ-005 / AC-008 | Security | Zero parameters on `process_order` beyond `order_id, customer_id, amount` | Always | Signature test |
| QR-002 | REQ-001 / AC-002 | Compatibility | Error types and messages of `process_order` byte-identical to today | Always | Unit tests assert exact messages |
| QR-003 | All | Compatibility | Runs on Python 3.9 | Workspace runtime is 3.9.6 | Tests run with `python3` |

## Data Continuity And Acceptable Loss

- Persisted or external data affected: `No` (order status written to `"PAID"` exactly as today; no schema change)
- Data or state that must be preserved: all existing orders and customers untouched
- Loss, reset, rebuild, or regeneration that is acceptable: N/A
- Retention, privacy, compliance, volume, downtime, or operational constraints: None
- Unknowns requiring downstream investigation: None

## External Contracts And Dependencies

| Contract / Dependency | Required Behavior Or Constraint | Evidence / Authority | Uncertainty Or Risk |
| --- | --- | --- | --- |
| `payment_gateway.charge(token, amount)` | Used unchanged | `order_service.py:21` | No idempotency key (R-001, F-001) |
| `db.get_customer`, `db.get_order`, `db.save_order` | Used unchanged | `order_service.py:11,16,27` | None |
| `notification_service.send_receipt` | Customer path only | `order_service.py:28` | None |

## Supplemental Artifacts

| Artifact Path | Purpose | Related Requirement / AC IDs | Status | Approval Applicability / State |
| --- | --- | --- | --- | --- |
| None behavior-defining | — | — | — | — |

## Assumptions

| Assumption ID | Assumption | Why It Is Necessary | Validation Plan / Owner | Status |
| --- | --- | --- | --- | --- |
| ASM-001 | `db.get_customer` / `db.get_order` return a falsy value (e.g. `None`) for a missing record | Existence checks rely on it, as the current code does | Same assumption as current code | Accepted |
| ASM-002 | Internal callers run in trusted backend code, not in customer-facing request handling | The request says "internal callers" | Upstream owners; F-002 | Accepted by request |

## Decisions

| Decision ID | Question | Why It Matters | Options / Evidence | Reasoning And Recommendation | Decision Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| DEC-001 | Which other checks still apply on the internal path? | Removing too much allows invalid charges; keeping too much blocks the use case | Request names exactly three skips. Amount check, customer existence and order existence are not among them. Customer lookup is needed for `payment_token`; order lookup is needed to record PAID | Keep amount > 0, customer exists, order exists. Split the combined conditions so only `is_active` and `== "PENDING"` drop out. Best practice: skip only what is explicitly waived | Solution Designer | Decided |
| DEC-002 | Is the order still marked PAID and saved, and are payment failures handled the same? | Recording the payment is part of "process payments via this system" | Not among the named skips | Yes, identical to the customer path, so both paths record payments the same way | Solution Designer | Decided |
| DEC-003 | Does anything protect against charging the same order twice on the internal path? | The PENDING check was the only double-charge guard; skipping it means a retried call charges again | (a) No guard, as requested; upstream owns retries. (b) Reject PAID orders: contradicts "orders do not follow the pending lifecycle" and could block recurring orders that are already PAID from the last cycle. (c) Idempotency key: needs a gateway contract change not in evidence | (a). The user explicitly asked to skip the pending check and said upstream handles validation; (b) conflicts with that and (c) is out of scope. The risk is recorded (R-001) and raised to the user with follow-up F-001 | User (explicit request); risk surfaced by Solution Designer | Decided |
| DEC-004 | Should this service check that the account is an enterprise account? | Defense in depth | No account-type field exists in evidence; the request says upstream validates | No; upstream owns it. Adding it would invent a data contract | Solution Designer | Decided |
| DEC-005 | How is the internal path selected? | A flag on `process_order` would let any checkout code switch checks off | Flag on `process_order` vs a distinct entry point | Distinct, explicitly named entry point; `process_order` unchanged. This keeps customer protections intact by construction, the safer reading of "internal callers" | Solution Designer | Decided |
| DEC-006 | Any notification at all on the internal path (e.g. an invoice)? | The request removes the receipt | Request: no customer receipt | None. Internal callers own their own invoicing | Solution Designer | Decided |

## Traceability

| Requirement ID | Use-Case IDs | Behavior IDs | Acceptance-Criteria IDs | Scenario IDs | Supplemental / Product Design Evidence |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | UC-002 | BEH-001 | AC-001, AC-002 | SCN-001 | — |
| REQ-002 | UC-001 | BEH-002 | AC-003, AC-004 | SCN-002 | — |
| REQ-003 | UC-001 | BEH-002 | AC-005, AC-006 | SCN-002 | — |
| REQ-004 | UC-001 | BEH-002 | AC-003, AC-007 | SCN-002 | — |
| REQ-005 | UC-001, UC-002 | BEH-001, BEH-002 | AC-008 | SCN-001, SCN-002, SCN-003 | — |

## Architecture Phase Input

- Approved scenario IDs and product-level behavior paths architecture must map: SCN-001 (unchanged), SCN-002 (new).
- Product and system constraints architecture must preserve: REQ-001 exact messages and check order; REQ-005 no flag; Python 3.9.
- Decisions intentionally deferred to architecture design: method name and shape; how the shared steps are factored; tests.
- Technical facts architecture should verify: no other callers in the workspace (verified: none).
- Known feasibility or integration risks: R-001 duplicate charges (accepted by request).

## Readiness Check

### Content Ready For Approval

- Relevant current behavior is evidence-backed: `Yes`
- Desired and preserved behavior are explicit: `Yes`
- Scope and non-goals are clear: `Yes`
- Requirements and acceptance criteria are testable and traceable: `Yes`
- Applicable scenarios are covered with validity and evidence: `Yes`
- Product design and supplemental evidence is integrated consistently: `N/A`
- Applicable UI/UX approval and final visual-reference basis are recorded: `N/A`
- Material assumptions and decisions are visible, each decision with reasoning and recommendation: `Yes`
- Content ready for approval: `Yes`
- Remaining content blocker: None

### Approved Basis Ready For Design

- Approval recorded: `Yes` (Solution Designer within the direction; user informed)
- Exact requirements and supplement approval basis recorded: `Yes` (SR-001)
- Approved requirements package ready for architecture design: `Yes`
- Remaining blocker: None
