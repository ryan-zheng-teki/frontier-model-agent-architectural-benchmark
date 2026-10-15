# Requirements Document — enterprise-internal-billing

## Document Status
- Status: Approved
- Current solution revision ID: SR-001
- Package identifier: enterprise-internal-billing
- Requested by: the user (direct request in conversation)
- Requirements owner: Solution Designer
- Date: 2026-10-15
- Approved by and reference: Solution Designer within the direction (user informed in the conversation reply that delivered this package)
- Approved baseline: this document at SR-001. No behavior-defining supplements.

## Problem And Desired Outcome
- Problem: internal recurring-billing and admin batch callers must charge pre-verified enterprise accounts via the payment gateway, but `process_order` forces the customer-active check, the pending-order check and the receipt.
- Desired outcome: a path to the same gateway that runs none of those three, with `process_order` unchanged.

## Scenarios
| ID | Class | Trigger / sequence / outcome | Evidence |
| --- | --- | --- | --- |
| SCN-001 | Supported Normal | Billing job (system event: subscription period due) charges an enterprise account for an amount it already validated and scored; gateway charge succeeds; job receives result. | User requirement text |
| SCN-002 | Supported Normal | Same trigger; gateway declines; caller gets a payment-failed error. | Existing decline behavior in `process_order` |
| SCN-003 | Supported Normal | Customer places a pending order and pays (existing). | `order_service.py` |
| SCN-004 | Unclear -> resolved by decision D-1..D-3 | Unknown account, zero/negative amount from internal caller. | See decisions |

## Behavior
| ID | Current | Desired | Preserved |
| --- | --- | --- | --- |
| BEH-001 | No internal path exists; internal callers cannot use `process_order` without the three checks. | Internal charge path with no customer-active check, no pending-order check, no receipt. | — |
| BEH-002 | `process_order`: amount>0, active customer, PENDING order, charge, mark PAID, save, receipt. | Unchanged. | All of it. |

## Scope Guardrail
- In scope: UC-001 internal enterprise charge (SCN-001, SCN-002, SCN-004).
- Out of scope: authentication/authorization of internal callers; gateway idempotency; audit logging; order-record updates for enterprise charges; changes to the gateway/db/notification interfaces; deactivated-account policy.
- Non-goals: preventing double charges from retried jobs.
- Preserved: BEH-002 / REQ-005 / AC-005.
- Review authority: findings must cite an approved REQ/AC; new policy proposals are Requirement Gaps.

## Requirements
| ID | Requirement | Behavior | Source |
| --- | --- | --- | --- |
| REQ-001 | Internal callers can charge an enterprise account via the gateway without the customer-active check. | BEH-001 | User |
| REQ-002 | ...without the order-pending check. | BEH-001 | User |
| REQ-003 | ...and no customer receipt is sent. | BEH-001 | User |
| REQ-004 | A declined charge raises the same `Payment failed: <error>` error as today. | BEH-001 | Consistency; decision D-4 |
| REQ-005 | `process_order` behavior is unchanged. | BEH-002 | User (implicit) |
| REQ-006 | Amount <= 0 is rejected before any lookup or charge. | BEH-001 | Decision D-1 |
| REQ-007 | An unknown account is rejected without charging. | BEH-001 | Decision D-2 |

## Acceptance Criteria
| ID | Criterion | REQ |
| --- | --- | --- |
| AC-001 | Charging an account with `is_active=False` succeeds and calls the gateway with its token. | REQ-001 |
| AC-002 | No order is read or saved on the internal path. | REQ-002 |
| AC-003 | The internal path has no notification dependency and sends no receipt. | REQ-003 |
| AC-004 | Declined charge raises `Payment failed: <error>`. | REQ-004 |
| AC-005 | Existing `process_order` success, inactive-customer, non-pending and decline outcomes are unchanged. | REQ-005 |
| AC-006 | Amount 0 or -1 raises `Amount must be positive`; gateway and db untouched. | REQ-006 |
| AC-007 | Unknown account raises ValueError; gateway not called. | REQ-007 |

## Decisions (owner: Solution Designer)
- D-1 Keep amount>0: not one of the three named checks; cheap money sanity check not covered by "fraud scoring".
- D-2 Customer lookup retained only to get the payment token; unknown account is an error.
- D-3 Order record not read/written: user says these orders do not follow the PENDING lifecycle, so no defined transition exists. Gateway result returned instead.
- D-4 Same decline error as today so callers handle one failure shape.
- Needs user: none. The explicit bypass of the three checks is the user's own instruction; the security consequences are surfaced to the user in the reply and DESIGN.md "Risks".
