# API/E2E Coverage Investigation

## Investigation Meta

- Requirements Doc: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/requirements-doc.md` (Approved, SR-001)
- Investigation Notes: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/investigation-notes.md`
- Solution Revision Record: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/solution-revision-record.md`
- Design Spec: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/design-spec.md` (SR-002, Ready)
- Supplemental Task Artifacts: `/Users/normy/Desktop/claude-test/DESIGN.md` (not behavior-defining)
- Design Review Report: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/design-review-report.md` (ARCH-REV-001, Pass)
- Architecture Review Revision Record: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/architecture-review-revision-record.md`
- Implementation Handoff: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/implementation-handoff.md` (IR-001)
- Implementation Revision Record: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/implementation-revision-record.md`
- Code Review Report: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/code-review-report.md` (CRR-001, Pass)
- Code Review Revision Record: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/code-review-revision-record.md`
- Delivery Revision Record / Relevant Delivery Revision IDs: N/A (no delivery re-entry)
- API/E2E Revision Record: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/api-e2e-revision-record.md`
- Current API/E2E Revision ID: `API-REV-001`
- API/E2E Test-Case Ledger: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/api-e2e-test-case-ledger.md`
- Current Investigation Round: 1
- Trigger: Code Review Pass CRR-001 from `/code_reviewer`
- Prior Investigation Reviewed: N/A
- Latest Authoritative Investigation: this file, round 1

## Routing Classification

- Task size: `Small`
- Architectural risk: `High`
- Input route: `Reviewed`
- Successful-output route: `Code Review` (per handoff rules)
- Proportional test-code review decision: `Not Applicable`. No durable test code was added, updated or removed in this round, so there is nothing to review. The reviewed route is otherwise kept.

## Current Requirement And Design Basis

These behaviors must be proven:

- REQ-001 (Critical): `process_order` must be byte-identical in behavior: same checks in the same order, the same exception types and messages, the same charge, PAID, save and receipt order, and the same signature.
- REQ-002 (Critical): `process_internal_enterprise_payment` charges the customer's token without the active check, without the PENDING check, and with no notification on any outcome.
- REQ-003 (High): it rejects a non-positive amount, a missing customer and a missing order with a `ValueError` before any charge.
- REQ-004 (High): success marks the order PAID and saves it. A failure raises `Exception("Payment failed: <error>")` and leaves the order unsaved and unchanged.
- REQ-005 (Critical): `process_order` has no parameter that relaxes its checks.

These are approved by design and are not defects: an already-PAID order is charged again (DEC-003, R-001/F-001), and inactive customers are charged (R-002).

## Supported Scenarios And Real Usage

- Designer scenarios covered: SCN-001 (customer checkout), SCN-002 (internal billing job or admin batch task).
- Real-use scenarios added from investigating the behavior:
  - SCN-002a: an admin batch task charges several enterprise accounts in sequence, and one charge is declined. The trigger is a sequence of `process_internal_enterprise_payment` calls. It proves that a failure is isolated per call and leaves that order unchanged.
  - SCN-002b: a recurring billing cycle runs again on orders already PAID by the previous cycle. Each order is charged again, as DEC-003 intends.
- Contrived scenarios, not tested: SCN-003 (customer-facing code switching checks off). AC-008 still pins the signature.

## Changed Behavior Summary

| Behavior ID / Boundary | Change Type | Upstream Evidence | Coverage Consequence |
| --- | --- | --- | --- |
| BEH-001 `process_order` (DS-001) | Preserved (internal refactor into shared steps) | REQ-001, design Removal Plan | Prove equivalence with the pre-change baseline, not only with the AC tests |
| BEH-002 `process_internal_enterprise_payment` (DS-002) | Added | REQ-002 to REQ-005 | Prove across all statuses and the active flag, every outcome, and no notification |
| `_charge_and_mark_paid` / `_require_positive_amount` | Added (shared private steps) | Design Ownership Map | Covered only through the public entry points |

## Changed Surface And Boundary Classification

| Surface / Boundary | Affected? | Actual Changed Boundary | Repository Evidence Available | Material Risk Not Exercised By That Evidence | Candidate Broader Validation Mode |
| --- | --- | --- | --- | --- | --- |
| Domain / backend logic | Yes | `OrderService` public methods | `test_order_service.py` (15 tests) | Tests use the permissive `Mock`, so an unexpected collaborator call would be absorbed silently | Strict-fake probe (Other) |
| API / transport / contract | No | No HTTP or RPC layer in the workspace | — | — | — |
| Frontend component / state | No | — | — | — | — |
| Browser integration / user journey | No | — | — | — | — |
| Authentication / session / permissions | No | No caller identity layer exists (F-002, out of scope) | — | — | — |
| Desktop renderer / web-equivalent UI | No | — | — | — | — |
| Desktop shell / Electron-specific integration | No | — | — | — | — |
| Process / lifecycle | No | — | — | — | — |
| Persisted-data transition | No (`Not Affected`) | The same `status="PAID"` write via `save_order` | Unit tests | None | — |
| Worker / queue / distributed coordination | No | No job runner in the workspace; the callers are external | — | Sequential batch and cycle use | Batch/cycle probe through the public method |
| External integration | Unchanged contract | Gateway, db, notifier used as before | Mocks only | Real gateway error shape (CAND-004, pre-existing, out of scope) | None available in the workspace |

## Project Execution Discovery

- Workspace: `/Users/normy/Desktop/claude-test` (non-git; edits in place)
- Project type and runtime stack: a single Python module, Python 3.9.6, stdlib `unittest`
- Project testing guideline: `No project testing guideline found` (no `TESTING*.md`, README, `AGENTS.md`, manifest or runner config)
- Conflicting, missing or unclear instructions: none. The command comes from design-spec Change Sequence step 4.
- Required environment variables or secrets: `N/A`

| Instruction / Configuration Path | Authority / Purpose | Commands, Setup, Or Constraints Learned |
| --- | --- | --- |
| `design-spec.md` → Change / Refactor Sequence | Test command | `python3 -m unittest -v` from the workspace root |
| `requirements-doc.md` QR-003 | Runtime | Python 3.9 (`python3` is 3.9.6) |

| Component / Dependency | Working Directory | Start / Setup Command | Runtime / Resource Notes | Readiness Check | Stop / Cleanup Method |
| --- | --- | --- | --- | --- | --- |
| Python 3.9.6 | workspace root; scratch `/tmp/iep-api-e2e` | none | stdlib only | `python3 --version` | Delete the scratch dir |

| Data / Fixture / Identity Need | Existing Project Mechanism Or Creation Method | Environment / Data-Safety Notes | Cleanup / Retention |
| --- | --- | --- | --- |
| Customers, orders, gateway results | In-memory `SimpleNamespace` objects and strict fakes in the probe | No shared or real data | In-process only |
| Pre-change baseline of `order_service.py` | The reviewer's `/private/tmp/order_service.baseline.py` no longer exists. I recovered it from the editor file history (`~/.claude/file-history/a83a8ffe-…/641e7a12f10a0328@v1`), and a second session's copy is byte-identical. It matches every line reference in the investigation notes (amount 9-10, charge 21, failure 22-23, PAID 26, save 27, receipt 28). | Read-only copy | Kept as `evidence/baseline-order_service.py` |

## Existing Durable Coverage Inventory

| Path / Test | Current Assertion Or Intent | Related Requirement / AC | Validity Decision | Evidence | Action |
| --- | --- | --- | --- | --- | --- |
| `test_order_service.py::ProcessOrderTests` (8 tests) | Checkout success, the 6 rejection and failure cases with exact messages and type, signature | REQ-001, REQ-005; AC-001, AC-002, AC-008 | Still Valid | Assertions match the approved messages and behavior | Keep |
| `test_order_service.py::ProcessInternalEnterprisePaymentTests` (7 tests) | Inactive customer with a PAID or ACTIVE order is charged; no notifications on any outcome; rejections; failure leaves ACTIVE unchanged; signature | REQ-002 to REQ-005; AC-003 to AC-008 | Still Valid | Same | Keep |

## Durable Coverage To Add

None. Every AC already has a direct, valid, mutation-sensitive durable test (C-06). The stricter checks (strict fakes, the baseline differential and the batch/cycle runs) depend on the baseline file outside the repository, or repeat the per-call durable assertions. They are run as temporary probes and kept as evidence.

## Durable Coverage To Update

None.

## Durable Coverage To Remove

None.

## Repository Coverage Execution Plan And Results

| Order | Command | Working Directory / Configuration | Boundary Or Scenario Proven | Result | Evidence / Output Path |
| --- | --- | --- | --- | --- | --- |
| 1 | `python3 -m unittest -v` | workspace root, Python 3.9.6 | AC-001 to AC-008, durable | Pass (15/15) | `evidence/C-01-unittest-full-suite.txt` |
| 2 | `python3 -I /tmp/iep-api-e2e/probes/probes.py <baseline> <current>` | `/tmp/iep-api-e2e` | C-02 to C-05 (see the ledger) | Pass (all checks) | `evidence/C-02-to-C-05-probe-output.txt`, `evidence/probe-script-probes.py` |
| 3 | 4 source mutants + durable suite; P-01 against a mutant | `/tmp/iep-api-e2e/mut` (deleted after) | Sensitivity of the durable suite and the differential probe | Pass (all detected) | `evidence/C-06-mutation-sensitivity.txt` |

## Test-Case Ledger Decision

- Ledger required: `Yes`. There are six independently meaningful cases (suite, differential, internal matrix, batch/cycle, checkout via strict fakes, mutation).
- Canonical ledger path: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/api-e2e-test-case-ledger.md`

## Post-Repository Confidence Scorecard

| Confidence Category | Score | What Supports The Score | Remaining Uncertainty | Additional Validation That Could Improve It |
| --- | --- | --- | --- | --- |
| Requirement and acceptance-criteria proof | 98% | All of AC-001 to AC-008 have direct durable tests plus independent probes. REQ-001 is proven against the real pre-change code on 120 combinations. | None material | — |
| Changed-boundary execution directness | 97% | The changed boundary is the public `OrderService` methods, and these are exercised directly. The workspace has no HTTP layer or job runner above them. | Real external callers are unknown (U-001, out of scope) | None in the workspace |
| Cross-boundary integration realism and mock gap | 92% | Strict fakes that expose only the observed collaborator contract (C-03 to C-05) show that no unexpected collaborator call happens on any path | Real gateway, db and notifier implementations are not in the workspace. Their contracts are unchanged (REQ "used unchanged"). The gateway `error` shape is CAND-004, pre-existing and out of scope. | Integration with real collaborators, which do not exist here |
| Environment, configuration, identity, and fixture fidelity | 95% | Target runtime Python 3.9.6 (QR-003). Deterministic in-memory fixtures. | No real data store | — |
| Failure, edge-case, lifecycle, and recovery evidence | 96% | Failure on every status × active flag; rejection precedence; batch with a declined account; repeat cycle | Non-string gateway error is excluded by instruction (CAND-004) | — |
| User-surface, browser, and desktop-shell confidence | N/A | Backend-only change with no UI (requirements: UI applicable `No`) | — | — |
| Durable regression coverage quality and relevance | 95% | 15 tests labelled by AC with exact type and message assertions. All 4 targeted mutants were caught. | The durable tests use the permissive `Mock`. Strict-fake checking exists only as a temporary probe. | Optional: strict fakes in durable tests (not needed for the ACs) |

- Overall post-repository confidence: 95.5%
- Calculation method: simple average of the 6 applicable categories
- Every critical acceptance criterion directly proven: `Yes`
- Any applicable category below 90%: `No`
- Default clean-confidence target of 95% met: `Yes`
- Material residual risks: none in scope. Accepted out-of-scope risks: R-001/F-001, R-002, U-001/F-002, CAND-004.

## Broader Validation Decision

- Decision: `Not Required`
- Selected execution mode: `None`. The strict-fake and batch probes are a temporary repository-level check.
- Specific confidence gap or residual risk addressed: N/A
- Browser-specific decision and rationale: not applicable. There is no browser, UI or transport surface.
- Evidence proving the real changed boundary without broader execution: the changed boundary is the `OrderService` public method layer. It is exercised directly (C-01 to C-05) with strict collaborator fakes, against the pre-change baseline, and in the real batch and cycle usage shape. The workspace contains no service, job runner or real collaborator that a broader run could start.

## Temporary Executable Validation Plan

| Case ID | Probe / Harness / Runtime Setup | Behavior Proven | Why This Should Not Remain As Durable Coverage |
| --- | --- | --- | --- |
| C-02 | Differential: baseline vs current `process_order`, 120 input combinations, strict fakes, full ordered call log | REQ-001 / QR-002 equivalence | Needs the pre-change file, which is not part of the repository |
| C-03 | Internal path × {PENDING, PAID, ACTIVE, CANCELLED} × active {T, F} × {success, failure}, plus rejection precedence | AC-003 to AC-007 | Repeats the durable per-AC tests in a matrix form |
| C-04 | Admin batch of 3 accounts (one declined) × 2 billing cycles | SCN-002a/b, AC-003/004/007, DEC-003 | Composition of per-call behavior already pinned durably |
| C-05 | Checkout through the same strict fakes | AC-001 call order | Repeats the durable AC-001 test |
| C-06 | 4 source mutants + durable suite; P-01 against a mutant | Durable suite and probe sensitivity | Mutation runs are a one-off quality check |

## Not Tested / Infeasible / Deferred

| Behavior / Boundary | Reason | Risk | Only The User Can Check? | Required Follow-Up Or Escalation |
| --- | --- | --- | --- | --- |
| Duplicate-charge protection | Out of scope (F-001); recharging is approved behavior | Cost | No | F-001 (existing) |
| Caller restriction of the internal method | Out of scope (F-002) | Security | No | F-002 (existing) |
| Non-string gateway `error` → `TypeError` | Pre-existing; REQ-001 keeps it; excluded by the reviewer (CAND-004) | Low | No | None |
| Real gateway, db and notifier | Not present in the workspace; contracts unchanged | Low | No | None |

## Ambiguities Or Reroute Triggers

None.

## Investigation Decision

- Proceed to API/E2E execution: `Yes` (executed)
- Durable coverage added, updated or removed: `No`
- Post-repository confidence: 95.5%
- Broader validation decision: `Not Required`
- Reroute required: `No`
