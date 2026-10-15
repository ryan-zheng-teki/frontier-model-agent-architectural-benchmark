# API/E2E Coverage Investigation — enterprise-internal-billing

## Investigation Meta

- Requirements Doc: /Users/normy/Desktop/claude-test/solution-package/requirements-doc.md
- Investigation Notes: /Users/normy/Desktop/claude-test/solution-package/investigation-notes.md
- Solution Revision Record: /Users/normy/Desktop/claude-test/solution-package/solution-revision-record.md
- Design Spec: /Users/normy/Desktop/claude-test/solution-package/design-spec.md
- Supplemental Task Artifacts: /Users/normy/Desktop/claude-test/DESIGN.md (non-normative rationale); solution-package/handoff.md
- Design Review Report: /Users/normy/Desktop/claude-test/solution-package/design-review-report.md
- Architecture Review Revision Record: /Users/normy/Desktop/claude-test/solution-package/architecture-review-revision-record.md
- Implementation Handoff: /Users/normy/Desktop/claude-test/solution-package/implementation-handoff.md
- Implementation Revision Record: /Users/normy/Desktop/claude-test/solution-package/implementation-revision-record.md
- Code Review Report: /Users/normy/Desktop/claude-test/solution-package/code-review-report.md
- Code Review Revision Record: /Users/normy/Desktop/claude-test/solution-package/code-review-revision-record.md
- Delivery Revision Record: N/A (not a delivery re-entry)
- API/E2E Revision Record: /Users/normy/Desktop/claude-test/solution-package/api-e2e-revision-record.md
- Current API/E2E Revision ID: API-REV-001
- API/E2E Test-Case Ledger: /Users/normy/Desktop/claude-test/solution-package/api-e2e-test-case-ledger.md
- Current Investigation Round: 1
- Trigger: Code review CRR-001 PASS (9.3/10, no findings) handoff
- Prior Investigation Reviewed: N/A
- Latest Authoritative Investigation: Round 1

## Routing Classification

- Task size: Small
- Architectural risk: High
- Input route: Reviewed
- Successful-output route: Code Review (proportional test-code review of changed durable tests)
- Proportional test-code review decision: Required

## Current Requirement And Design Basis

Behavior to prove: `EnterpriseBillingService.charge_account(customer_id, amount)` (REQ-001..004, 006, 007) charges through the same gateway using the stored token, ignoring `is_active`, never reading/saving orders, having no notifier, raising `Payment failed: <error>` on decline, rejecting amount <= 0 before any lookup/charge, and rejecting unknown accounts without charging. `OrderService.process_order` must be unchanged apart from calling `_charge_or_raise` (REQ-005/AC-005). Accepted non-blocking risks ARCH-REV-001 R-1..R-6 (caller authorization, double-charge/audit, inactive chargeable by design, NaN, mock-only evidence) get no added coverage without an approved REQ/AC.

## Supported Scenarios And Real Usage

- Designer scenarios covered: SCN-001 (job charges inactive/active enterprise account), SCN-002 (decline), SCN-003 (customer order pays via `process_order`), SCN-004 (unknown account, 0/-1 amount).
- Real-use scenarios added: a recurring-billing job iterating over accounts (mix of active, inactive, unknown, declined, zero amount) calling `charge_account` once per account through a stateful in-memory db and a stateful recording gateway, where one failure must not alter other accounts' outcomes (job's per-account try/except is the caller's own; the service just raises). Also a mixed-traffic scenario: customer `process_order` and an internal charge run against the same db/gateway objects, proving the internal path leaves orders untouched while the customer path still marks PAID.
- Recorded `Technically Possible but Unsupported/Contrived`: none recorded by designer. Not tested: concurrency/double-charge races (R-2), authorization (R-1), NaN (R-4).

## Changed Behavior Summary

| Behavior ID / Boundary | Change Type | Upstream Evidence | Coverage Consequence |
| --- | --- | --- | --- |
| BEH-001 / `charge_account` | Added | requirements-doc, design-spec S-2 | Boundary tests with stateful fakes (not MagicMock) |
| BEH-002 / `process_order` | Preserved (helper extraction) | design-spec S-1 | Differential test vs. reconstructed original (no git baseline), plus mixed-traffic scenario |
| `_charge_or_raise` | Added (shared) | design-spec | Exercised via both paths |

## Changed Surface And Boundary Classification

| Surface / Boundary | Affected? | Actual Changed Boundary | Repository Evidence Available | Material Risk Not Exercised By That Evidence | Candidate Broader Validation Mode |
| --- | --- | --- | --- | --- | --- |
| Domain / backend logic | Yes | service methods in order_service.py | 9 MagicMock unit tests | Mocks accept any call; ordering/state not observed | Stateful-fake boundary tests (selected) |
| API / transport / contract | No | no transport exists in repo | — | — | — |
| Frontend / browser / desktop (all four rows) | No | none exist | — | — | — |
| Authentication / session / permissions | No (out of scope R-1) | — | — | Accepted risk | — |
| Process / lifecycle | No | — | — | — | — |
| Persisted-data transition | No (Not Affected) | — | — | — | — |
| Worker / queue / distributed | No | — | — | — | — |
| External integration | Yes (gateway/db contract by usage) | `gateway.charge(token, amount)` returning `.success/.error`; `db.get_customer/get_order/save_order` | mocks only | No real gateway/db exists in the repo or environment | Contract-faithful in-memory fakes; real gateway cannot be safely provided |

## Project Execution Discovery

- Assigned task worktree / workspace: /Users/normy/Desktop/claude-test (not a git repository)
- Project type and runtime stack: single-file Python 3.9.6 module, stdlib `unittest`
- Project testing guideline path(s): No project testing guideline found (no TESTING*.md, README, manifests, CI config; checked directory listing)
- Conflicting, missing, or unclear project instructions: none exist; derived commands from implementation handoff / code review (`python3 -B -m unittest test_order_service`)
- Required environment variables or secrets available: N/A (none required; no real gateway)

| Instruction / Configuration Path | Authority / Purpose | Commands, Setup, Or Constraints Learned |
| --- | --- | --- |
| implementation-handoff.md, code-review-report.md | Run command | `cd /Users/normy/Desktop/claude-test && python3 -B -m unittest test_order_service` |
| investigation-notes.md E-1 | Original `process_order` logic | Basis to reconstruct pre-change behavior (no git baseline) |

| Component / Dependency | Working Directory | Start / Setup Command | Runtime / Resource Notes | Readiness Check | Stop / Cleanup Method |
| --- | --- | --- | --- | --- | --- |
| In-memory fake db / recording gateway / recording notifier | /Users/normy/Desktop/claude-test | created inside tests | pure Python, no I/O, no ports | n/a | garbage collected |

| Data / Fixture / Identity Need | Existing Project Mechanism Or Creation Method | Environment / Data-Safety Notes | Cleanup / Retention |
| --- | --- | --- | --- |
| Enterprise accounts (inactive, active), unknown id, PENDING/PAID orders | Built in test setUp | No production or shared data touched | None needed |

## Persisted Data Transition Coverage Basis

- Approved decision: Not Affected. No persisted data touched; nothing to prove.

## Existing Durable Coverage Inventory

| Path / Test | Current Assertion Or Intent | Related Req / AC | Validity Decision | Evidence | Action |
| --- | --- | --- | --- | --- | --- |
| test_order_service.py `ProcessOrderPreservedTests` (4 tests) | pin process_order happy/inactive/non-pending/decline | REQ-005 / AC-005 | Still Valid | assertions match approved current behavior; code reviewed | Keep; supplement with differential test |
| test_order_service.py `EnterpriseBillingTests` (5 tests) | AC-001..004, 006, 007 with MagicMock | REQ-001..004,006,007 | Still Valid | match requirements | Keep; supplement with stateful boundary tests |

## Durable Coverage To Add

| Case ID | Behavior / Boundary | Evidence | Planned Path | Why Durable |
| --- | --- | --- | --- | --- |
| TC-001 | Billing-job scenario: inactive account charged, gateway receives stored token and amount, result returned (AC-001) | REQ-001 | test_enterprise_billing_boundary.py | MagicMock accepts anything; fakes verify real state |
| TC-002 | Internal charge leaves order store untouched; no notifier exists; no order reads (AC-002, AC-003) | REQ-002/003 | same | observe order-store state and call log |
| TC-003 | Decline raises `Payment failed: <error>` with identical type/message as process_order on same gateway; no state change (AC-004) | REQ-004 | same | cross-path consistency |
| TC-004 | amount 0 / -1 rejected with no db/gateway calls (AC-006) | REQ-006 | same | call-log proof of "before any lookup" |
| TC-005 | Unknown account rejected, gateway call log empty (AC-007) | REQ-007 | same | |
| TC-006 | Batch job over mixed accounts: per-account outcomes independent, exact gateway call log | SCN-001/002/004 | same | real-use journey |
| TC-007 | Mixed traffic on shared db/gateway: process_order marks PAID + receipt; enterprise charge for another account does not alter orders/receipts | SCN-003, REQ-005 | same | |
| TC-008 | Differential: `process_order` vs. reconstructed original (pre-change) over matrix of amount/customer/order/gateway outcomes — same result or exception type+message, same gateway calls, same db writes, same receipts | REQ-005 / AC-005 | same | No git baseline; original reconstructed from investigation-notes E-1 and design-spec |

## Durable Coverage To Update / Remove

None.

## Repository Coverage Execution Plan And Results

1. `python3 -B -m unittest test_order_service` (existing, narrowest).
2. `python3 -B -m unittest test_enterprise_billing_boundary` (new).
3. `python3 -B -m unittest discover -p "test_*.py"` (whole suite).
Results recorded in the execution coverage report and ledger.

## Temporary Executable Validation Plan

| Case ID | Probe | Behavior Proven | Why Not Durable |
| --- | --- | --- | --- |
| TP-001 | Mutation probe: temporarily mutate a copy of order_service.py (e.g. add `is_active` check, add `get_order` call, drop amount check, drop unknown-account check) in a temp dir and confirm new tests fail | Tests have teeth, not tautological | Mutation scaffolding is verification of tests, not product behavior |

## Not Tested / Infeasible / Deferred

| Behavior / Boundary | Reason | Risk | Only The User Can Check? | Follow-Up |
| --- | --- | --- | --- | --- |
| Real payment gateway / real database | None exist in repo; no credentials; charging real money is unsafe | Contract assumed from usage (`charge(token, amount)` -> `.success/.error`) | Yes (real gateway/db wiring belongs to the user's deployment) | Delivery notes it |
| R-1 authorization, R-2 double-charge/audit, R-3 inactive policy, R-4 NaN | Accepted risks, no approved REQ/AC | Accepted by ARCH-REV-001 | No | None; do not add without approved REQ/AC |

## Ambiguities Or Reroute Triggers

None.

## Investigation Decision

- Proceed To API/E2E Execution: Yes
- Repository-Resident Durable Coverage Will Be Added / Updated / Removed: Yes (add one test file)
- Post-repository confidence: filled in execution report after runs
- Broader validation decision: Not Required beyond the stateful-boundary tests: no browser/desktop/transport surface exists and no real gateway/db is available; the added boundary tests are the closest safe surface.
- Reroute Required Before Validation Execution: No
- Notes: Round 1.
