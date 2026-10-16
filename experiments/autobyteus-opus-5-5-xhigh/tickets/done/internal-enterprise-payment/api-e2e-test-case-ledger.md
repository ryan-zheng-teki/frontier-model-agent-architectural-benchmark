# API/E2E Test-Case Ledger

## Ledger Meta

- Assigned task workspace: `/Users/normy/Desktop/claude-test` (non-git)
- Coverage investigation: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/api-e2e-coverage-investigation.md`
- Execution coverage report: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/api-e2e-execution-coverage-report.md`
- API/E2E revision record: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/api-e2e-revision-record.md`
- Ledger scope and reason it is required: six independent cases (round 1, API-REV-001)
- Last updated: 2026-10-16

## Planned Cases

| Case ID | Case / Journey | Requirement / AC IDs | Boundary / Execution Surface | Planned Command Or Entry Point | Planned Order | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| C-01 | Durable unit suite | AC-001 to AC-008 | `OrderService` public methods | `python3 -m unittest -v` (workspace root) | 1 | Durable |
| C-02 | Baseline differential for `process_order` | REQ-001, AC-001, AC-002, QR-002 | `process_order` | `probes.py` P-01 | 2 | Temporary |
| C-03 | Internal path matrix with strict fakes | AC-003 to AC-007 | `process_internal_enterprise_payment` | `probes.py` P-02 | 3 | Temporary |
| C-04 | Admin batch + second billing cycle | SCN-002a/b; AC-003, AC-004, AC-007 | `process_internal_enterprise_payment` | `probes.py` P-03 | 4 | Temporary |
| C-05 | Checkout through strict fakes | AC-001 | `process_order` | `probes.py` P-04 | 5 | Temporary |
| C-06 | Mutation sensitivity | AC-002, AC-003, AC-004, AC-007 | Durable suite + P-01 | 4 mutants in `/tmp/iep-api-e2e/mut` | 6 | Temporary |

## Execution Events

| Sequence | Case ID | Timestamp | Event | Command / Entry Point / Material Configuration | Expected Observable Result | Observed Result Or Checkpoint | Result | Evidence / Artifact Path | Next Action / Unresolved Issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | C-01 | 2026-10-16 | Completed | `python3 -m unittest -v`, Python 3.9.6 | 15 OK | `Ran 15 tests … OK` | Pass | `evidence/C-01-unittest-full-suite.txt` | — |
| 2 | C-02 | 2026-10-16 | Completed | `python3 -I probes.py baseline current` | Identical results on every combination | 120/120 identical (outcome, exception type and message, ordered call log, final status) | Pass | `evidence/C-02-to-C-05-probe-output.txt` | — |
| 3 | C-03 | 2026-10-16 | Completed | same run | Success → PAID, saved, no notify; failure → exact `Exception`, status unchanged, no save, no notify; rejections → `ValueError` before charge | 16 success/failure + 4 rejection checks pass | Pass | same | — |
| 4 | C-04 | 2026-10-16 | Completed | same run | s1, s2 charged each cycle; s3 fails with the exact message and stays ACTIVE; 6 charges, 4 saves, 0 notifications | As expected | Pass | same | — |
| 5 | C-05 | 2026-10-16 | Completed | same run | charge → save(PAID) → receipt | As expected | Pass | same | — |
| 6 | C-06 | 2026-10-16 | Completed | 4 mutants | Every mutant caught | M1 to M4 each fail the durable suite; P-01 flags 40 mismatches against M4 | Pass | `evidence/C-06-mutation-sensitivity.txt` | — |

## Re-entry And Reconciliation

- Last durably recorded event: sequence 6, C-06 Completed
- Last completed case and result: C-06 Pass
- Cases still running, interrupted or not started: none
- Next case or recovery action: none
- Reconciled into execution coverage report: `Yes`, Test-Case Ledger Reconciliation section
