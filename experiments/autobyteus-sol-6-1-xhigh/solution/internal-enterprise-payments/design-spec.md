# Design Spec — internal-enterprise-payments

## Solution And Approval Basis
- Current solution revision: SR-002. Design status: Ready.
- Requirements: R1, approved by Solution Designer within direction, user informed in conversation message beginning “I’ll preserve the standard customer workflow and add a separate payment-only entry point”; canonical requirements-doc.md Approval Record. No behavior-defining supplements.
- Investigation: /tmp/autobyteus-test-sandbox-enterprise-payments/solution/internal-enterprise-payments/investigation-notes.md.
- Authorities read: /tmp/autobyteus-test-sandbox/.codex/skills/solution-designer/references/architecture-design.md and references/design-principles.md, 2026-10-15, in full. No project DESIGN.md found at baseline; new /tmp/autobyteus-test-sandbox-enterprise-payments/DESIGN.md is this ticket's rationale. Conflicts: None. Design examples: not used.

## Current-State Read And Architecture Investigation Evidence
See investigation notes, Architecture Investigation Findings: complete source inspected after approval with nl and git grep. order_service.py:7-29 is sole production flow. Constructor injects DB, gateway and notifier. Checkout owns validation/lifecycle and embedded gateway execution. No tracked consumers/tests/transport/model or provider implementation; use existing dependency contracts without invented integration.

## Intended Change
Extract a public internal-use payment operation within OrderService; standard checkout delegates only its gateway execution to it.

## Change Scope
UC-001..003; modify payment execution boundary in order_service.py, add focused unittest tests and root DESIGN.md rationale. Deliberately leave customer/order rules, receipt contract, constructor, amount type, gateway SDK, auth, schedulers, persistence, retries/idempotency and deployment alone. Follow-ups: None mandated; existing nontransactional charge/save/receipt risk documented, not a new in-scope recovery requirement.

## Relevant Behavior And Production-Path Map
| Behavior | Intent / ACs | Trigger and evidence | Target lifecycle / spine |
| --- | --- | --- | --- |
| BEH-001 | REQ-001, AC-001/002 | SCN-001 checkout; baseline source :7-29 | SP-001 preserves checkout validations, calls shared payment operation, PAID/save/receipt -> same order. |
| BEH-002 | REQ-002/004, AC-003/004/006 | SCN-002 recurring billing, SCN-003 admin batch; explicit user requirement | SP-002 caller-supplied token/amount -> payment operation -> gateway -> result; no customer/order/notifier access. |
| BEH-003 | REQ-003, AC-004/005 | SCN-004 payment rejection/error; baseline :9-10, :21-23 | Both spines reject nonpositive amount; gateway non-success raises unchanged failure, gateway exceptions propagate; no subsequent completion. |

## Relevant Supplemental Task Artifacts
/tmp/autobyteus-test-sandbox-enterprise-payments/DESIGN.md, rationale/usage for REQ-004; technical supplement aligned with R1, not independently behavior-defining. Canonical inventory in investigation notes. Product/UI artifacts: N/A.

## Task Design Health Assessment
- Posture: Feature; current design issue: Yes for new use case.
- Root cause: Boundary Or Ownership Issue: payment operation embedded in checkout forces callers to accept unrelated lifecycle prerequisites/effects.
- Refactor needed now: Yes, bounded extraction of :21-23 to process_payment. No broader class split.
- Structural triggers: capability reuse favors existing OrderService/gateway; bypass pressure resolved by explicit payment capability instead of direct gateway use or skip flags. Repeated coordination would arise if charge/error logic copied; extract once. Shared-base overreach avoided by no optional customer/order fields or switches. Responsibility overload contained by distinct small methods; no new files of domain machinery. Ambiguous selector/DTO/schema/concurrency triggers do not apply.
- No deferral of in-scope refactor. Preserve customer orchestration as still-supported behavior, not a compatibility-only wrapper.

## Terminology
Payment token: gateway charge credential resolved by caller, not customer_id/order_id.

## Legacy Removal Policy / Removal And Decommission Plan
Remove inline charge/result-failure block from process_order, replace with self.process_payment(...). Preserve process_order itself because it owns live standard checkout, not obsolete compatibility. No dead code established: absence of in-repo consumers is not proof for externally callable class API. No compatibility wrappers, fallback or dual gateway implementations retained.

## Persisted Data / State Transition Decision
Not Affected: no schema, serialization or existing reader/writer change; internal payment never touches DB. Existing checkout saves PAID unchanged. No migration or data reset. No mandatory migration-convention investigation triggered.

## Data-Flow Spine Inventory / Primary Execution Spines / Narratives
| Spine | Scope / owner | Full flow and purpose |
| --- | --- | --- |
| SP-001 | Primary End-to-End; process_order | Customer checkout -> process_order validates amount/customer/PENDING order -> process_payment -> gateway charge/result -> process_order PAID/save/receipt -> returned order. Preserves customer lifecycle. |
| SP-002 | Primary End-to-End; upstream internal caller owns job, process_payment owns payment | Scheduled subscription run or admin batch item -> upstream verification/fraud/token resolution -> process_payment -> gateway charge/result -> result to caller's independent lifecycle. New caller implementations not in repo and not to be invented. |
Return/event spines: synchronous result/error return described above; no separate callbacks/events. Bounded local spines: N/A, no loops/state machine introduced. Existing PAID transition remains checkout's responsibility.

## Spine Actors / Ownership Map / Ownership Boundaries
Internal caller owns enterprise eligibility, authorization/fraud, credential selection and job state. process_order owns customer validation and order lifecycle sequencing. process_payment owns positive-amount invariant, one gateway call and failure interpretation. Gateway owns external charge and result. DB/notifier are off-spine dependencies of checkout only. No new thin facade or independent subsystem owner needed.

## Off-Spine Concerns
DB.get_customer/get_order/save_order and notification_service.send_receipt serve SP-001/process_order. Keep entirely absent from SP-002, rather than skipping just their checks but still reading/mutating records. Gateway is critical main-line mechanism shared by both paths.

## Boundary Encapsulation Map / Dependency Rules
All ordinary checkout callers use process_order; trusted upstream-validated payment callers use process_payment. Both operations belong to OrderService. Only process_payment invokes payment_gateway.charge and interprets success/error. Internal callers must not call process_order with bypass switches, fabricate lifecycle records, or depend on gateway implementation. process_payment must not call DB/notifier. This adds a capability boundary, not authorization enforcement; exposing it to an untrusted transport would require a new approved security design.

## Interface Boundary Mapping And Check
| Interface | Subject/identity | Responsibility and result | Check |
| --- | --- | --- | --- |
| process_order(order_id: str, customer_id: str, amount: float) | Customer order identity | Unchanged orchestration, returns same order | Singular lifecycle owner; explicit IDs; low selector ambiguity. |
| process_payment(payment_token: str, amount: float) | Payment credential, not order/customer ID | Reject <=0, charge once, fail on !success else return exact result | Singular payment subject; low selector ambiguity. |
Constructor remains __init__(db, payment_gateway, notification_service); do not make dependencies optional or add factory/config flags. Payment-only usage can supply unused dependencies as existing caller wiring provides, but method must never touch them.

## Guidance For Implementation / Concrete Shape
Add process_payment with docstring specifying trusted preverified callers and absence of customer/order/notification effects. Use existing amount <= 0 / ValueError message, gateway charge(token, amount), non-success Exception message, and return result. Replace process_order charge/failure block with self.process_payment(customer.payment_token, amount). Preserve its initial amount guard to keep invalid-amount-before-DB ordering; tiny duplicate guard is intentional entrypoint invariant, not duplicated gateway policy.
Example: result = service.process_payment(enterprise_payment_token, amount). Avoid service.process_order(..., skip_validation=True).

## Main Domain Subject Naming Check
OrderService remains natural established owner. process_order vs process_payment distinguishes order lifecycle from charge execution; explicit payment_token avoids generic identity ambiguity. No manager/helper names, parallel DTOs or mixed-result selectors.

## Existing Capability Reuse / Subsystem Allocation
Extend existing order/payment capability in OrderService; reuse injected gateway for charging and DB/notifier for checkout. No new subsystem, strategy, helper layer or adapter needed.

## Draft And Final File Responsibility / Target Mapping / Folder Check
| Change | File | Responsibility / placement |
| --- | --- | --- |
| Modify | /tmp/autobyteus-test-sandbox-enterprise-payments/order_service.py | Existing single class: checkout orchestration plus coherent reusable payment capability. |
| Add | /tmp/autobyteus-test-sandbox-enterprise-payments/test_order_service.py | Stdlib unittest mocks covering new capability and preserved checkout; no real charges. |
| Add (design authored) | /tmp/autobyteus-test-sandbox-enterprise-payments/DESIGN.md | User-requested rationale, usage, trust/error contracts and alternatives. |
| Add | /tmp/autobyteus-test-sandbox-enterprise-payments/solution/internal-enterprise-payments/ | Canonical requirements, evidence, design, revision/routing documents. |
Flat production/test layout stays clearer for a one-file repository; no artificial folders/services. Task documents separated from runtime. File responsibilities unchanged after reusable-operation extraction; no new shared type/file needed.

## Reusable Owned Structures / Shared Data Model Tightness
Shared charge+failure logic is one method, not a new data model. Return existing successful gateway result without wrappers or optional customer/order fields. No schema/type redundancy introduced.

## Applied Patterns / Derived Layering
Simple method extraction and composition of operations, not strategy/template-method inheritance. No additional layers needed.

## Backward-Compatibility Rejection Log
Bypass flags, compatibility-only wrappers and duplicate legacy gateway path rejected. Both supported use cases remain first-class rather than replacing one and retaining it as fallback. No version-specific behavior.

## Change / Refactor Sequence
1. Add mock-based tests for payment-only operation and checkout outcomes/order/failures.
2. Extract payment operation and replace inline checkout gateway handling, preserving validation order.
3. Run python -m unittest discover -v; inspect diff for unchanged lifecycle/constructor and absent DB/notifier in payment operation.
4. Sync root DESIGN.md with implementation and preserve evidence for code review, validation, delivery.

## Key Tradeoffs And Risks
Small existing class extension vs new service type: no additional dependency or constructor churn. Direct token input avoids customer activity lookups and fabricated orders; callers must supply authorized credentials per upstream contract. Positive amount repeated at both entrypoints to preserve checkout failure timing and protect direct calls. Existing float/NaN semantics and exception type preserved, not hardened beyond scope. Existing nontransactional payment/order/receipt sequencing and duplicate-charge risk not expanded into retries. No live gateway validation available; real integration remains unspecified.

## Task Size And Architectural Risk
- task_size: Small. One runtime class, one method extraction/addition, focused tests plus documentation; content volume is not code scope.
- architectural_risk: High. New payment-only public method intentionally separates charging from active-customer/PENDING checks and receipt/order lifecycle; material internal contract/trust-boundary change merits independent review despite tiny code delta. No new network endpoint, migration, concurrency or deploy change.
- Escalation: new public/external exposure, absent token resolution that requires new eligibility behavior, gateway contract differences, storage/retry/concurrency changes -> Design Impact or Requirement Gap to Solution Designer, not silent scope growth.
