# API/E2E Test-Case Ledger — enterprise-internal-billing

## Ledger Meta
- Assigned task workspace: /Users/normy/Desktop/claude-test (not a git repository)
- Coverage investigation: /Users/normy/Desktop/claude-test/solution-package/api-e2e-coverage-investigation.md
- Execution coverage report: /Users/normy/Desktop/claude-test/solution-package/api-e2e-execution-coverage-report.md
- API/E2E revision record: /Users/normy/Desktop/claude-test/solution-package/api-e2e-revision-record.md
- Scope / reason: 8 durable cases plus one mutation probe, one round.
- Last updated: 2026-10-15

## Planned Cases
| Case ID | Case | Req / AC | Surface | Entry Point | Order |
| --- | --- | --- | --- | --- | --- |
| TC-001 | Inactive account charged with stored token | REQ-001 / AC-001 | stateful fakes | test_enterprise_billing_boundary.EnterpriseChargeBoundaryTests.test_tc001 | 1 |
| TC-002 | No order access, no notifier | REQ-002,003 / AC-002,003 | same | ...test_tc002 | 2 |
| TC-003 | Decline error identical to customer path | REQ-004 / AC-004 | same | ...test_tc003 | 3 |
| TC-004 | amount<=0 rejected before any call | REQ-006 / AC-006 | same | ...test_tc004 | 4 |
| TC-005 | Unknown account rejected | REQ-007 / AC-007 | same | ...test_tc005 | 5 |
| TC-006 | Billing job mixed batch | SCN-001/002/004 | same | ...test_tc006 | 6 |
| TC-007 | Mixed customer + internal traffic | SCN-003 / REQ-005 | same | ...test_tc007 | 7 |
| TC-008 | process_order differential vs. reconstructed original (96 combinations) | REQ-005 / AC-005 | same | ProcessOrderDifferentialTests.test_tc008_matrix | 8 |
| TP-001 | Mutation probe (9 mutants) | test strength | temp copy | /tmp/mutate_probe.py | 9 |

## Execution Events
| Seq | Case | Event | Command | Expected | Observed | Result | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | existing 9 unit tests | Completed | `python3 -B -m unittest -v test_order_service` | OK | Ran 9, OK | Pass | evidence/run1-existing-unit.txt |
| 2 | TC-001..TC-008 | Completed | `python3 -B -m unittest -v test_enterprise_billing_boundary` | OK | Ran 8, OK | Pass | evidence/run2-boundary.txt |
| 3 | full suite | Completed | `python3 -B -m unittest discover -v -p "test_*.py"` | OK | Ran 17, OK | Pass | evidence/run3-full-suite.txt |
| 4 | TP-001 | Completed | `python3 -I /tmp/mutate_probe.py ...` | all mutants killed | 9/9 killed by both files | Pass | evidence/mutation-probe-results.txt |

## Re-entry And Reconciliation
- Last completed case and result: TP-001 Pass
- Cases still running / not started: none
- Reconciled into execution coverage report: Yes — Changed Boundary And Evidence Matrix
