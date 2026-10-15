# Design Spec

## Solution And Approval Basis
- Package internal-enterprise-payments; SR-002; Design Ready / Architecture Design Complete.
- Requirements: /tmp/autobyteus-internal-payments/solution/requirements-doc.md, approved SR-001 by Solution Designer within direction; approval reference recorded there. No changed intent.
- Investigation: /tmp/autobyteus-internal-payments/solution/investigation-notes.md.
- Authorities read (2026-10-15): /tmp/autobyteus-test-sandbox/.codex/skills/solution-designer/references/{architecture-design,design-principles}.md and design-spec template. No project DESIGN.md found at intake; newly authored /tmp/autobyteus-internal-payments/DESIGN.md is the requested rationale. No conflicts; examples reference N/A.

## Current-State Read And Architecture Investigation Evidence
Post-approval `nl -ba order_service.py` confirms all execution in a 29-line synchronous class; lines 21–23 own gateway invocation and failure translation inside customer lifecycle orchestration. Investigation source log and post-approval findings are canonical evidence. No concrete external collaborators, callers, stored models or infrastructure supplied.

## Intended Change
Extract payment execution as a public token-based operation; customer orchestration calls it after unchanged validation and state checks. Internal callers invoke it directly without customer/order lifecycle coupling.

## Change Scope
UC-001/002/003: modify only payment execution ownership in order_service.py, add focused tests and root DESIGN.md rationale. Deliberately leave constructor, process_order signature, customer checks and status/save/receipt sequencing intact. No scheduler, auth framework, account classification, retry, money representation or migration additions. Follow-ups: None established by supplied repository; existing recovery limitations are documented, not new implementation obligations.

## Relevant Behavior And Production-Path Map / Data-Flow Spine Inventory
| Spine | Approved behavior and IDs | Primary end-to-end path | Governing owner/outcome |
|---|---|---|---|
| DS-001 | BEH-001, SCN-001, UC-001, REQ-001/003, AC-001/003 | Scheduled billing event → upstream verified account/token → process_payment → gateway.charge → gateway outcome returned to job | Job owns eligibility/accounting, service owns charge invocation/failure translation |
| DS-002 | BEH-002, SCN-002, UC-002, REQ-001/003, AC-001/003 | Admin batch trigger → upstream verified account/token → process_payment → gateway.charge → payment outcome returned to batch | Same service capability; upstream batch owns iteration/lifecycle |
| DS-003 | BEH-003, SCN-003, UC-003, REQ-002/003, AC-002/003 | Customer request → process_order positive amount/customer/order checks → process_payment → gateway.charge → process_order PAID/save/receipt → returned order | OrderService owns customer lifecycle; DB/notification remain injected collaborators |

## Spine Narratives / Actors And Ownership
DS-001: after upstream subscription verification, the job passes token and amount; the service validates only amount, charges once and returns the result or raises. No DB or notification use. DS-002 is independently supported by the administrative event and uses the same payment boundary; no batch implementation is invented. DS-003 retains the ordered existing checks, delegates only payment execution, then performs existing state/notification effects. Returned result and errors are synchronous; additional return/event or bounded-loop spines N/A (no async or loop in this service).

## Task Design Health Assessment
Feature; current issue Yes relative to new capability: Boundary Or Ownership Issue. Payment execution is embedded in an order-only method, making existing customer lifecycle mandatory. Refactor needed now: Yes, bounded extraction only. Authoritative-boundary trigger: callers need a supported payment operation rather than direct gateway access outside the service. Repeated-coordination risk avoided by extracting rather than copying charge handling. Ambiguous-ID trigger avoided with explicit token parameter, not an overloaded customer/order identifier. No file overload/shared structure/persistence transition trigger: small existing owner still adequate. Broader class split would be empty indirection for this scope.

## Ownership Boundaries / Boundary Encapsulation / Dependency Rules
- Public process_order owns customer checks, pending-state eligibility, persistence, receipt and returned order. Its caller must not use payment-only operation to process ordinary customer orders.
- Public process_payment owns positive-amount invariant, gateway call, failure-result translation, returned payment result. It is trusted in-process API, not authentication. Internal jobs own authorization and pre-verification; callers obtain tokens upstream.
- Allowed: process_order → process_payment → injected gateway; internal job → process_payment. Forbidden new coupling: process_payment → db/notification/process_order; duplicate direct charge path left in process_order; customer-controlled skip flags.
- No separate thin facade or off-spine subsystem: N/A. Existing DB and notification collaborators serve process_order unchanged. Gateway owns actual payment processing.

## Interface Boundary Mapping And Checks
| Interface | Explicit identity/subject | Responsibility and return | Check |
|---|---|---|---|
| process_order(order_id: str, customer_id: str, amount: float) | Separate order and customer IDs | Existing customer workflow; return order | Singular orchestration, no generic selectors |
| process_payment(payment_token: str, amount: float) | Gateway payment token, not customer/order ID | Charge one payment; return original gateway result | Singular payment capability; no flags |
Method naming remains domain-specific; unchanged class name appropriate for small current file. Payment result stays the existing gateway object; no DTO or optional-field hierarchy needed.

## Exact Implementation Guidance
1. Add process_payment with existing `amount <= 0`/ValueError guard. Invoke `self.payment_gateway.charge(payment_token, amount)` exactly once. If not result.success, raise existing `Exception("Payment failed: " + result.error)`; return result on success. Let gateway exceptions propagate.
2. Replace process_order's existing inline gateway call and failure branch with `self.process_payment(customer.payment_token, amount)`; retain its earlier amount check to preserve rejection before DB calls. Rechecking positive amount at the reusable boundary is deliberate, minimal and deterministic.
3. Leave post-charge status/save/receipt/return untouched. No exception wrapping, retries, floats overhaul, new batch/account model or DB reads in the payment-only method.
4. Docstring makes trusted upstream eligibility and absence of customer/order side effects explicit.
Example: `result = service.process_payment(enterprise_payment_token, invoice_amount)`. Avoid `process_order(..., skip_checks=True)`.

## Legacy Removal Policy / Removal-Decommission Plan
Remove inline charge and failure translation from process_order; replaced by process_payment. No compatibility wrapper, dual payment execution, fallback, or deprecated methods. No dead code identified: constructor and existing method are public API even though external consumers are not present. Existing supported customer flow is not obsolete.

## Persisted Data / State Transition Decision
Not Affected: no model, serialization, storage or invariant changes; original customer status PAID/save behavior preserved; payment-only operation uses no persistence. Migration plan N/A. Storage volume/concrete engine unknown but immaterial to this no-transformation design.

## Subsystem Reuse / File Responsibility / Structures / Folder Checks
Reuse and extend existing OrderService, gateway, DB and notification contracts. No new subsystem. Draft and final mapping identical: one source file remains coherent after method extraction; no repeated DTO/normalizer/schema to extract. Shared-structure checks N/A (no model introduced). Flat root appropriate to one small module; no artificial layers/directories.

## Target Subsystem / Folder / File Mapping
| Change/path | Responsibility | Must not contain |
|---|---|---|
| Modify order_service.py | Payment-only operation and existing customer orchestration sharing it | Skip flags, duplicate gateway path, new auth/batch framework |
| Add test_order_service.py | stdlib unittest mocks/fakes; AC-001–003 including effect ordering and no internal DB access | Real payment/network credentials |
| Add DESIGN.md | REQ-004/AC-004 rationale, usage, trust limits and alternatives | Claims of implemented auth or guaranteed idempotency |
| Add solution/*.md | Approved intent, evidence, design, revision and handoff context | Changes to runtime policy outside requirements |

## Backward-Compatibility Rejection Log
Skip-flags/dual implementations rejected: separate subject-level methods sharing one implementation instead. Existing process_order retained as current supported workflow, not a compatibility-only wrapper. No legacy fallback mechanisms.

## Change / Refactor Sequence
Implement extracted operation and replace inline gateway handling; add focused unit/regression tests; sync DESIGN.md to implemented API; specialist validation and delivery finalize locally into original checkout. No deployment/live charge required.

## Verification Intent / Key Tradeoffs / Risks
Test zero/negative amounts in both paths; missing/inactive customer and missing/nonpending order; standard happy-path ordered effects and identity return; internal exact token/amount and result identity with db/notification unusable; unsuccessful gateway result and raised gateway exception in both paths, no later customer effects. Use stdlib unittest to avoid new dependencies.
Minimal extraction avoids sprawling flags/classes but OrderService construction still accepts irrelevant DB/notification collaborators for internal-only usage; do not alter constructor contract for this ticket. Small duplicated amount check preserves original validation ordering and protects the independent capability. Gateway settlement/auth enforcement cannot be established from this fixture; mocks validate seam behavior only. Existing post-charge save/receipt failure ambiguity unchanged.

## Relevant Supplements
/tmp/autobyteus-internal-payments/DESIGN.md: technical rationale owned here, REQ-004, no independent behavior supplement. Product N/A. Independent reviews N/A — not applicable yet (routing pending; not claiming review bypass).

## Task Size And Architectural Risk
- task_size: Small. One 29-line runtime file, one test file, requested rationale; solution documents are not runtime scope.
- architectural_risk: High. Explicit new payment-only contract intentionally omits customer safeguards and separates lifecycle ownership. Despite bounded implementation and user authorization, this is material contract/trust-boundary behavior, warranting independent classification/routing rather than calling it content-only or Low.
- Escalation trigger: any need for actual job integration, account eligibility/auth API, DB changes, retry semantics, or altered customer behavior returns as Design Impact/Requirement Gap; do not broaden silently.
