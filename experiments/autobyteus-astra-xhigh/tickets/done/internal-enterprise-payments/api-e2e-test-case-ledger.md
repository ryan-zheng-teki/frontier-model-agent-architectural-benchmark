# API/E2E Test-Case Ledger

## Ledger Meta
Workspace /tmp/autobyteus-internal-payments. Round 1, API-REV-001 planned. Canonical investigation, execution coverage report and revision record: corresponding api-e2e-*.md files under solution/. Required for multiple independent cases. Initialized before execution, 2026-10-15.

## Planned Cases
| Case | Entry / journey | Requirement | Order |
| --- | --- | --- | --- |
| API-001 | test_order_service.PaymentTests.test_success_returns_exact_result_and_charges_once | AC-001/003 | 1 |
| API-002 | test_order_service.PaymentTests.test_nonpositive_amount_rejected_before_charge | AC-001/003 | 2 |
| API-003 | test_order_service.PaymentTests.test_unsuccessful_result_uses_existing_exception | AC-001/003 | 3 |
| API-004 | test_order_service.PaymentTests.test_gateway_exception_propagates_unchanged | AC-001/003 | 4 |
| API-005 | test_order_service.CustomerOrderTests.test_success_preserves_full_sequence_state_and_return_identity | AC-002/003 | 5 |
| API-006 | test_order_service.CustomerOrderTests.test_nonpositive_amount_stops_before_all_dependencies | AC-002/003 | 6 |
| API-007 | test_order_service.CustomerOrderTests.test_missing_or_inactive_customer_stops_before_order_lookup | AC-002/003 | 7 |
| API-008 | test_order_service.CustomerOrderTests.test_missing_or_nonpending_order_stops_before_charge | AC-002/003 | 8 |
| API-009 | test_order_service.CustomerOrderTests.test_unsuccessful_payment_stops_before_mutation_save_and_receipt | AC-002/003 | 9 |
| API-010 | test_order_service.CustomerOrderTests.test_gateway_exception_propagates_without_customer_effects | AC-002/003 | 10 |
| API-011 | Full documented unittest suite | AC-001–003 regression | 11 |
| API-012 | DESIGN.md source-correlated inspection | AC-004 | 12 |

## Execution Events
| Sequence | Case | Timestamp UTC | Event | Command / expected | Observed / result | Evidence | Next |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | API-001 | 2026-10-15T19:05:51.934370+00:00 | Started | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.PaymentTests.test_success_returns_exact_result_and_charges_once; expected all assertions pass | N/A | evidence/API-001.txt | Run |
| 2 | API-001 | 2026-10-15T19:05:51.985123+00:00 | Completed | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.PaymentTests.test_success_returns_exact_result_and_charges_once; expected all assertions pass | Pass; exit 0 | evidence/API-001.txt | Next planned case |
| 3 | API-002 | 2026-10-15T19:05:51.985154+00:00 | Started | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.PaymentTests.test_nonpositive_amount_rejected_before_charge; expected all assertions pass | N/A | evidence/API-002.txt | Run |
| 4 | API-002 | 2026-10-15T19:05:52.029828+00:00 | Completed | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.PaymentTests.test_nonpositive_amount_rejected_before_charge; expected all assertions pass | Pass; exit 0 | evidence/API-002.txt | Next planned case |
| 5 | API-003 | 2026-10-15T19:05:52.029856+00:00 | Started | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.PaymentTests.test_unsuccessful_result_uses_existing_exception; expected all assertions pass | N/A | evidence/API-003.txt | Run |
| 6 | API-003 | 2026-10-15T19:05:52.080378+00:00 | Completed | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.PaymentTests.test_unsuccessful_result_uses_existing_exception; expected all assertions pass | Pass; exit 0 | evidence/API-003.txt | Next planned case |
| 7 | API-004 | 2026-10-15T19:05:52.080421+00:00 | Started | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.PaymentTests.test_gateway_exception_propagates_unchanged; expected all assertions pass | N/A | evidence/API-004.txt | Run |
| 8 | API-004 | 2026-10-15T19:05:52.134614+00:00 | Completed | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.PaymentTests.test_gateway_exception_propagates_unchanged; expected all assertions pass | Pass; exit 0 | evidence/API-004.txt | Next planned case |
| 9 | API-005 | 2026-10-15T19:05:52.134646+00:00 | Started | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.CustomerOrderTests.test_success_preserves_full_sequence_state_and_return_identity; expected all assertions pass | N/A | evidence/API-005.txt | Run |
| 10 | API-005 | 2026-10-15T19:05:52.180341+00:00 | Completed | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.CustomerOrderTests.test_success_preserves_full_sequence_state_and_return_identity; expected all assertions pass | Pass; exit 0 | evidence/API-005.txt | Next planned case |
| 11 | API-006 | 2026-10-15T19:05:52.180376+00:00 | Started | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.CustomerOrderTests.test_nonpositive_amount_stops_before_all_dependencies; expected all assertions pass | N/A | evidence/API-006.txt | Run |
| 12 | API-006 | 2026-10-15T19:05:52.225147+00:00 | Completed | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.CustomerOrderTests.test_nonpositive_amount_stops_before_all_dependencies; expected all assertions pass | Pass; exit 0 | evidence/API-006.txt | Next planned case |
| 13 | API-007 | 2026-10-15T19:05:52.225178+00:00 | Started | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.CustomerOrderTests.test_missing_or_inactive_customer_stops_before_order_lookup; expected all assertions pass | N/A | evidence/API-007.txt | Run |
| 14 | API-007 | 2026-10-15T19:05:52.268917+00:00 | Completed | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.CustomerOrderTests.test_missing_or_inactive_customer_stops_before_order_lookup; expected all assertions pass | Pass; exit 0 | evidence/API-007.txt | Next planned case |
| 15 | API-008 | 2026-10-15T19:05:52.268946+00:00 | Started | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.CustomerOrderTests.test_missing_or_nonpending_order_stops_before_charge; expected all assertions pass | N/A | evidence/API-008.txt | Run |
| 16 | API-008 | 2026-10-15T19:05:52.314090+00:00 | Completed | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.CustomerOrderTests.test_missing_or_nonpending_order_stops_before_charge; expected all assertions pass | Pass; exit 0 | evidence/API-008.txt | Next planned case |
| 17 | API-009 | 2026-10-15T19:05:52.314119+00:00 | Started | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.CustomerOrderTests.test_unsuccessful_payment_stops_before_mutation_save_and_receipt; expected all assertions pass | N/A | evidence/API-009.txt | Run |
| 18 | API-009 | 2026-10-15T19:05:52.358312+00:00 | Completed | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.CustomerOrderTests.test_unsuccessful_payment_stops_before_mutation_save_and_receipt; expected all assertions pass | Pass; exit 0 | evidence/API-009.txt | Next planned case |
| 19 | API-010 | 2026-10-15T19:05:52.358343+00:00 | Started | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.CustomerOrderTests.test_gateway_exception_propagates_without_customer_effects; expected all assertions pass | N/A | evidence/API-010.txt | Run |
| 20 | API-010 | 2026-10-15T19:05:52.404815+00:00 | Completed | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service.CustomerOrderTests.test_gateway_exception_propagates_without_customer_effects; expected all assertions pass | Pass; exit 0 | evidence/API-010.txt | Next planned case |
| 21 | API-011 | 2026-10-15T19:05:52.404845+00:00 | Started | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service; expected all assertions pass | N/A | evidence/API-011.txt | Run |
| 22 | API-011 | 2026-10-15T19:05:52.450019+00:00 | Completed | PYTHONDONTWRITEBYTECODE=1 python -m unittest -v test_order_service; expected all assertions pass | Pass; exit 0 | evidence/API-011.txt | Next planned case |
| 23 | API-012 | 2026-10-15T19:06:09.241058+00:00 | Started | Read DESIGN.md and correlate with source/REQ-004; expect boundaries, usage, trust, preservation, alternatives | N/A | evidence/API-012.txt | Inspect |
| 24 | API-012 | 2026-10-15T19:06:09.241322+00:00 | Completed | Read DESIGN.md and correlate with source/REQ-004; expect boundaries, usage, trust, preservation, alternatives | Pass; all AC-004 content present and source-consistent | evidence/API-012.txt | Finalize report |

## Re-entry And Reconciliation
Last durably recorded event: 24, API-012 Completed Pass, 2026-10-15. Cases API-001–012 all completed Pass. No running, interrupted, failed, blocked or unstarted cases. Every case completion persisted before the next case. No rerun/prior failure. Reconciled: Yes, api-e2e-execution-coverage-report.md Test-Case Ledger Reconciliation. Next: completed result handoff.
