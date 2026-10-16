# Design Spec

## Solution And Approval Basis

- Current solution revision ID: `SR-002`
- Approved requirements baseline / revision, who approved, and approval reference: `requirements-doc.md` at `SR-001`; approved by Solution Designer within the direction, user informed (Solution Designer message to the user, 2026-10-16)
- Behavior-defining supplements and their approval references: None
- Design status: `Ready`
- Canonical investigation-notes path: `/Users/normy/Desktop/claude-test/tickets/internal-enterprise-payment/investigation-notes.md`
- Authorities read (design reading gate; file and date): `references/architecture-design.md`, `references/design-principles.md` (2026-10-16, each opened in full by path); `references/design-examples.md` sections: Example 1, Example 10, Example 11, Common Bad-Practice Patterns, How To Use These Examples; `No project DESIGN.md found` (this ticket creates `/Users/normy/Desktop/claude-test/DESIGN.md` at the user's request)
- Project design-principle conflicts with the general principles, or discrepancies: None (no project principles existed)

## Current-State Read

`OrderService.process_order` (`order_service.py:7-29`) is the only payment entry point and the single owner of the sequence: amount check → customer lookup + active check → order lookup + PENDING check → gateway charge → mark PAID + save → receipt. Two conditions each combine "the record must exist" with "customer-lifecycle policy" (`not customer or not customer.is_active`; `not order or order.status != "PENDING"`). The internal path needs the first half of each without the second. The class is small (30 lines), has injected collaborators, no callers or tests in the workspace, and no other structural problems. See BEH-001/BEH-002 and the Architecture Investigation Findings in the investigation notes.

## Task Size And Architectural Risk (Mandatory)

- Task size: `Small`
- Size rationale and supporting evidence: one production file (`order_service.py`, about 30 → 55 lines), one new test file, one new project document. One owner (`OrderService`), no new subsystem, no persistence or deployment change.
- Architectural risk: `High`
- Risk rationale and supporting evidence: the change adds a new public contract on the payment owner that deliberately relaxes two safeguards: the customer active-status check and the PENDING check, which today is also the only protection against charging the same order twice (R-001). Under the principles' standard, a material new security contract makes the risk `High` even though the code delta is small. Who may call the new entry point is a security boundary that this workspace cannot enforce (U-001, F-002).
- Escalation trigger if implementation or validation discovers new impact: any need to change `process_order`'s signature or messages, to touch the gateway contract (idempotency), to add caller authentication, or evidence that customer-facing code reaches `OrderService` methods generically (by name or reflection). Each returns a `Design Impact` or `Requirement Gap` to Solution Designer.

## Architecture Investigation Evidence

| Source / Command / Probe | Exact Path / Reference | Observation | Design Decision Supported | Remaining Uncertainty |
| --- | --- | --- | --- | --- |
| Code read | `order_service.py:7-29` | Single owner of the charge sequence; combined existence/lifecycle conditions | Keep `OrderService` as owner; split conditions only in the new path; share the charge-and-record step | None |
| `grep -rn "process_order\|OrderService" --include=*.py .` | workspace | No callers or tests | No caller migration; new tests needed | External callers (U-001) |
| `python3 --version` | — | 3.9.6 | Stdlib `unittest` + `unittest.mock`; no 3.10+ syntax | None |
| Gateway usage | `order_service.py:21-23` | No idempotency parameter | Duplicate-charge protection left to upstream (DEC-003), follow-up F-001 | Gateway capabilities unknown |

## Intended Change

Add a second, explicitly named public entry point on `OrderService` for internal enterprise charges. It keeps the amount check and the customer/order existence checks, skips the customer active check, the PENDING check and the receipt, and shares one private charge-and-record step with `process_order`. `process_order` keeps its exact behavior and signature.

## Change Scope (Mandatory)

- In scope: UC-001 (internal enterprise charge) and UC-002 (customer checkout, protected). Areas: `OrderService` in `order_service.py`; new unit tests; new project `DESIGN.md`.
- Deliberately left alone: `process_order`'s signature, checks, order of checks and messages (REQ-001); the gateway, store and notification contracts; any caller authentication layer (none exists here); enterprise/fraud checks (upstream owns them per the request).
- Follow-ups:
  - F-001 (urgent, cost risk): duplicate-charge protection for internal callers. With the PENDING check gone, a retried internal job charges the same order again. Suggested Task: "Add idempotency to internal enterprise charges, e.g. an idempotency key per billing cycle passed to the gateway, or a per-cycle charge record checked before charging." Evidence: R-001, `order_service.py:16-18` (the PENDING check was the only guard), the gateway call has no idempotency key (`order_service.py:21`).
  - F-002 (security): make sure only internal billing jobs and admin batch tasks can reach `process_internal_enterprise_payment`. For example, give customer-facing composition only the customer-facing surface, or expose the internal method through a separate interface, and add a deployment-boundary check if internal and customer code share a process. Evidence: U-001; the workspace has no caller identity or authorization layer.

## Relevant Behavior And Production-Path Map (Mandatory)

| Behavior ID | Kind | Approved Requirement / Intent And Acceptance-Criteria IDs | Approved Trigger Or Governing Contract | Relevant Existing Behavior And Evidence Reference | Approved Change Or Preserved Outcome | Target Production Path / Lifecycle And Spine ID(s) |
| --- | --- | --- | --- | --- | --- | --- |
| BEH-001 | User | REQ-001, REQ-005; AC-001, AC-002, AC-008 | Customer checkout calls `process_order` (SCN-001) | `order_service.py:7-29` | Preserved exactly | DS-001 |
| BEH-002 | System / Operational | REQ-002–REQ-005; AC-003–AC-008 | Internal billing job or admin batch task calls `process_internal_enterprise_payment` (SCN-002) | No current supported behavior | New | DS-002 |

SCN-003 (customer-facing code switching off checks) is `Technically Possible but Unsupported/Contrived` as a supported path; the design rules it out by construction (no parameter on `process_order` relaxes anything), and the remaining deployment-level exposure is follow-up F-002.

## Relevant Supplemental Task Artifacts

| Artifact Path | Purpose | Related Requirement / Acceptance-Criteria IDs (When Applicable) | Relationship To This Design | Status / Approval Applicability |
| --- | --- | --- | --- | --- |
| `/Users/normy/Desktop/claude-test/DESIGN.md` | User-requested design rationale; project design document for later tasks | All | Summarizes this design and records the project rule "no check-skipping flags on payment entry points" | Current; not behavior-defining |

## Task Design Health Assessment (Mandatory)

- Change posture: `Feature`
- Current design issue found: `No`
- Structural triggers that fire, each with evidence; if none fire, name the triggers this change could plausibly hit and the evidence ruling each out:
  - Repeated coordination / duplicated policy: would fire if the new path copied the charge, failure handling and PAID update. Ruled out by sharing one private `_charge_and_mark_paid` step.
  - Ambiguous-boundary (one method serving two policies through a flag): would fire with `process_order(..., skip_checks=True)`. Ruled out: two explicitly named entry points, each with one policy.
  - Empty indirection: a separate `InternalBillingService` class that only forwards to `OrderService` would own nothing. Ruled out: the new entry point lives on the existing owner.
  - Responsibility overload: `OrderService` grows to about 55 lines with one subject (charging an order); not overloaded.
- Root cause classification: `No Design Issue Found`
- Refactor needed now: `No` (only the extraction of the shared charge step, which is part of adding the feature cleanly, not a refactor of existing debt)
- Evidence: `order_service.py` is small, single-owner, with injected collaborators; no callers or tests depend on its internals.
- Design response: extend the existing owner with a second named entry point and one shared private step.
- Refactor rationale: N/A
- Intentional deferrals and residual risk, if any: F-001 (duplicate charges), F-002 (caller restriction). Both are outside the approved scope; the in-scope behavior is coherent without them.

## Terminology

- Customer checkout payment: `process_order`, the existing path with all customer protections.
- Internal enterprise charge: `process_internal_enterprise_payment`, the new path for internal billing jobs and admin batch tasks.

## Section Fill Order

Followed as listed in the template.

## Legacy Removal Policy (Mandatory)

- Obsolete legacy paths and files in this scope: None. `process_order` stays the customer path; nothing it does becomes obsolete.
- Compatibility wrappers, dual paths, or legacy fallbacks this design keeps: `None`. The two entry points are two supported use cases, not an old and a new version of one.

## Persisted Data / State Transition Decision (Mandatory When Persisted Data May Be Affected)

- Decision: `Not Affected`. The internal path writes `status = "PAID"` through `db.save_order` exactly as the customer path does. No schema, field or stored meaning changes.

## Data-Flow Spine Inventory

| Spine ID | Scope | Related Behavior ID(s) | Start | End | Governing Owner | Why It Matters |
| --- | --- | --- | --- | --- | --- | --- |
| DS-001 | `Primary End-to-End` | BEH-001 | Customer checkout | Receipt sent; PAID order returned | `OrderService.process_order` | Must stay unchanged |
| DS-002 | `Primary End-to-End` | BEH-002 | Internal billing job / admin batch task | PAID order returned, no notification | `OrderService.process_internal_enterprise_payment` | New path with relaxed checks |

## Primary Execution Spine(s)

- DS-001: `Customer checkout -> OrderService.process_order -> [amount, customer exists+active, order exists+PENDING] -> _charge_and_mark_paid -> PaymentGateway.charge -> db.save_order -> NotificationService.send_receipt`
- DS-002: `Billing job / batch task -> OrderService.process_internal_enterprise_payment -> [amount, customer exists, order exists] -> _charge_and_mark_paid -> PaymentGateway.charge -> db.save_order`

## Spine Narratives (Mandatory)

| Spine ID | Short Narrative | Main Domain Subject Nodes | Governing Owner | Key Off-Spine Concerns |
| --- | --- | --- | --- | --- |
| DS-001 | Checkout asks to pay a pending order. The service enforces customer protections in the same order as today, then the shared step charges the token and records PAID, then the receipt goes out. | Customer, Order, payment | `OrderService` | Receipt notification |
| DS-002 | An internal job asks to charge an enterprise account for an order in any status. The service checks only that the amount is positive and the customer and order exist, then the same shared step charges and records PAID. Nothing is sent. | Customer, Order, payment | `OrderService` | None |

## Spine Actors / Main-Line Nodes

Caller (checkout or internal job) → `OrderService` entry point → `_charge_and_mark_paid` → `payment_gateway` → `db`.

## Ownership Map

- `OrderService.process_order`: owns the customer-path policy (active customer, PENDING order, receipt).
- `OrderService.process_internal_enterprise_payment`: owns the internal-path policy (existence only, no notification).
- `OrderService._require_positive_amount`: owns the amount invariant and its message, shared by both paths.
- `OrderService._charge_and_mark_paid`: owns the charge, failure handling and PAID recording, shared by both paths. Both entry points are governing owners of their own policy, not thin facades.

## Thin Entry Facades / Public Wrappers (If Applicable)

N/A. Both public methods own policy.

## Removal / Decommission Plan (Mandatory)

| Item To Remove / Decommission | Why It Becomes Unnecessary | Replaced By Which Owner / File / Structure | Scope | Notes |
| --- | --- | --- | --- | --- |
| Inline charge/PAID/save lines in `process_order` (lines 20–27) | Moved, not removed: now the shared `_charge_and_mark_paid` | `OrderService._charge_and_mark_paid` | In This Change | Behavior identical |
| Inline amount check (lines 9–10) | Moved into the shared `_require_positive_amount` | `OrderService._require_positive_amount` | In This Change | Same message |
| Dead code in touched file | None: every line of `order_service.py` is reached by `process_order` | — | — | Checked by reading the 30-line file |

## Return Or Event Spine(s) (If Applicable)

N/A. Synchronous return of the order, or a raised exception.

## Bounded Local / Internal Spines (If Applicable)

N/A. No loop or state machine.

## Off-Spine Concerns Around The Spine

| Off-Spine Concern | Related Spine ID(s) | Serves Which Owner | Responsibility | Why It Exists | Risk If Misplaced On Main Line |
| --- | --- | --- | --- | --- | --- |
| Receipt notification | DS-001 | `process_order` | Email receipt | Customer path only | If placed in the shared step, internal charges would send receipts (violates REQ-002) |

## Ownership Boundaries

`OrderService` is the authoritative boundary for charging an order. Callers use one of its two public entry points and never call the gateway or `db.save_order` directly for payments. The two private methods are internal mechanisms behind both entry points.

## Boundary Encapsulation Map

| Authoritative Boundary | Internal Owned Mechanism(s) It Encapsulates | Upstream Callers That Must Use The Boundary | Forbidden Bypass Shape | If Boundary API Is Too Thin, Fix By |
| --- | --- | --- | --- | --- |
| `OrderService.process_order` | `_require_positive_amount`, `_charge_and_mark_paid`, receipt | Customer checkout | Checkout calling `process_internal_enterprise_payment` or the private methods | Not applicable |
| `OrderService.process_internal_enterprise_payment` | `_require_positive_amount`, `_charge_and_mark_paid` | Internal billing jobs, admin batch tasks | Internal jobs calling `payment_gateway.charge` directly, or calling `_charge_and_mark_paid` | Not applicable |

## Dependency Rules

- Customer-facing code may depend on `process_order` only.
- Internal billing jobs and admin batch tasks may depend on `process_internal_enterprise_payment`.
- Nobody outside `OrderService` calls its private methods.
- Forbidden: a parameter on `process_order` that relaxes its checks or its receipt; copying the charge-and-record logic into a second place.

## Interface Boundary Mapping

| Interface / API / Query / Command / Method | Subject Owned | Responsibility | Accepted Identity Shape(s) | Notes |
| --- | --- | --- | --- | --- |
| `process_order(order_id: str, customer_id: str, amount: float) -> order` | Customer payment of a pending order | Unchanged | `order_id`, `customer_id` | Signature frozen (AC-008) |
| `process_internal_enterprise_payment(order_id: str, customer_id: str, amount: float) -> order` | Internal enterprise charge | New | `order_id`, `customer_id` | Same identity shape as `process_order` so callers pass the same data |

## Interface Boundary Check

| Interface | Responsibility Is Singular? | Identity Shape Is Explicit? | Ambiguous Selector Risk | Corrective Action |
| --- | --- | --- | --- | --- |
| `process_order` | Yes | Yes | Low | None |
| `process_internal_enterprise_payment` | Yes | Yes | Low | None |

## Main Domain Subject Naming Check

| Node / Subject | Current / Proposed Name | Name Is Natural And Self-Descriptive? | Naming Drift Risk | Corrective Action |
| --- | --- | --- | --- | --- |
| Internal entry point | `process_internal_enterprise_payment` | Yes: says internal and enterprise, so a reviewer sees a customer-facing caller is wrong | Low | None |
| Shared charge step | `_charge_and_mark_paid` | Yes | Low | None |
| Amount invariant | `_require_positive_amount` | Yes | Low | None |

## Existing Capability / Subsystem Reuse Check

| Need / Concern | Existing Capability Area / Subsystem | Decision | Why | If New, Why Existing Areas Are Not Right |
| --- | --- | --- | --- | --- |
| Charge and record | `OrderService` | Extend | Already owns it | — |
| Gateway, store | Injected collaborators | Reuse | Unchanged contracts | — |

## Subsystem / Capability-Area Allocation

| Subsystem / Capability Area | Owns Which Concerns | Related Spine ID(s) | Governing Owner(s) Served | Decision | Notes |
| --- | --- | --- | --- | --- | --- |
| Order payment (`OrderService`) | Both entry-point policies; shared charge step | DS-001, DS-002 | — | Extend | — |

## Draft File Responsibility Mapping

| Candidate File | Owning Subsystem / Capability Area | Owner / Boundary | Concrete Concern | Why This Is One File | Reuses Shared Structure? |
| --- | --- | --- | --- | --- | --- |
| `order_service.py` | Order payment | `OrderService` | Both entry points + shared steps | One owner, one subject, about 55 lines | Yes (`_charge_and_mark_paid`) |
| `test_order_service.py` | Tests | — | AC-001–AC-008 | Tests for one class | — |

## Reusable Owned Structures Check

| Repeated Structure / Logic | Candidate Shared File | Owning Subsystem | Why Shared | Redundant Attributes Removed? | Overlapping Representations Removed? | Must Not Become |
| --- | --- | --- | --- | --- | --- | --- |
| Charge → failure → PAID → save | `order_service.py` (`_charge_and_mark_paid`) | Order payment | Both paths must record payments identically (REQ-004) | Yes | Yes | A place that sends notifications or checks lifecycle |
| Amount > 0 check | `order_service.py` (`_require_positive_amount`) | Order payment | One message, one rule | Yes | Yes | A general validation helper |

## Shared Structure / Data Model Tightness Check

N/A. No data structures are added or changed.

## Final File Responsibility Mapping

Same as the draft mapping.

## Applied Patterns (If Any)

None.

## Target Subsystem / Folder / File Mapping

| Path | Kind | Owner / Boundary | Responsibility | Why It Belongs Here | Must Not Contain |
| --- | --- | --- | --- | --- | --- |
| `/Users/normy/Desktop/claude-test/order_service.py` | File (Modify) | `OrderService` | Both entry points, `_require_positive_amount`, `_charge_and_mark_paid` | Existing owner | A skip flag; notification in the shared step |
| `/Users/normy/Desktop/claude-test/test_order_service.py` | File (Add) | Tests | `unittest` tests for AC-001–AC-008 with `unittest.mock` doubles | Next to the module, as the workspace is flat | Tests of private methods |
| `/Users/normy/Desktop/claude-test/DESIGN.md` | File (Add) | Project design | Design rationale and payment entry-point rule | User asked for it at the root | Ticket process detail |

The flat layout matches the workspace (one module); adding folders would create structure with no owner.

## Folder Boundary Check

| Path / Folder | Intended Structural Depth | Ownership Boundary Is Clear? | Mixed-Layer Or Over-Split Risk | Justification / Corrective Action |
| --- | --- | --- | --- | --- |
| workspace root | `Mixed Justified` | Yes | Low | One module, one test file, one doc |

## Concrete Examples / Shape Guidance (Mandatory When Needed)

| Topic | Good Example | Bad / Avoided Shape | Why The Example Matters |
| --- | --- | --- | --- |
| Selecting the internal path | `service.process_internal_enterprise_payment(order_id, customer_id, amount)` | `service.process_order(order_id, customer_id, amount, skip_checks=True)` | A flag on the customer method can be passed from any checkout code (one request field away from a bypass); a named method can be found with grep and kept out of customer code |
| Sharing the charge | both entry points call `self._charge_and_mark_paid(customer, order, amount)` | two copies of `charge` / `if not success` / `PAID` / `save` | Copies drift; e.g. a later change to failure handling made in only one path |

Target shape (illustrative; the implementation engineer owns the final code):

```python
def process_order(self, order_id: str, customer_id: str, amount: float):
    self._require_positive_amount(amount)
    customer = self.db.get_customer(customer_id)
    if not customer or not customer.is_active:
        raise ValueError("Invalid or inactive customer")
    order = self.db.get_order(order_id)
    if not order or order.status != "PENDING":
        raise ValueError("Order is not in pending state")
    self._charge_and_mark_paid(customer, order, amount)
    self.notification_service.send_receipt(customer.email, order)
    return order

def process_internal_enterprise_payment(self, order_id: str, customer_id: str, amount: float):
    self._require_positive_amount(amount)
    customer = self.db.get_customer(customer_id)
    if not customer:
        raise ValueError("Customer not found")
    order = self.db.get_order(order_id)
    if not order:
        raise ValueError("Order not found")
    self._charge_and_mark_paid(customer, order, amount)
    return order
```

## Backward-Compatibility Rejection Log (Mandatory)

| Candidate Compatibility Mechanism | Why It Was Considered | Rejection Decision | Clean-Cut Replacement / Removal Plan |
| --- | --- | --- | --- |
| `skip_checks` / `internal=True` flag on `process_order` | Smallest diff | Rejected | Separate named entry point (REQ-005) |

## Derived Layering (If Useful)

N/A.

## Change / Refactor Sequence

1. Add `test_order_service.py` with AC-001/AC-002 against the current `process_order` and confirm they pass (a baseline that proves REQ-001 is preserved).
2. Extract `_require_positive_amount` and `_charge_and_mark_paid`; re-run the baseline tests.
3. Add `process_internal_enterprise_payment`; add AC-003–AC-008 tests.
4. Run `python3 -m unittest -v` from the workspace root.

## Key Tradeoffs

- Method on the existing class vs a separate service class: a separate class would give stronger separation through dependency injection, but with one 30-line owner and no composition root in evidence it would be an empty forwarding layer or would split one charge policy across two owners. The named method is the proportionate choice; stronger separation is follow-up F-002.
- No duplicate-charge guard on the internal path: matches the explicit request; cost risk recorded as R-001/F-001.

## Risks

- R-001 duplicate charges on retry (accepted by request; F-001).
- R-002 inactive accounts charged (accepted by request; upstream owns).
- U-001 customer-facing code reaching the internal method (F-002).

## Guidance For Implementation

- Keep `process_order` messages byte-identical and its check order unchanged; AC-002 asserts exact strings.
- `_charge_and_mark_paid` must raise before mutating the order on failure (as today: status is set only after success).
- No notification call anywhere on the internal path, including on failure.
- Do not add parameters to `process_order`.
- Python 3.9: stdlib `unittest` and `unittest.mock` only.
