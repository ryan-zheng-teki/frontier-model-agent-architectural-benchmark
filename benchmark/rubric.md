# Benchmark Evaluation Rubric: Architectural Integrity vs. Test-Hacking Bloat

## 1. Background & Motivation

Current frontier models (Sonnet 5.5, Opus 5.5, Sol 6.1, Gemini 3.8, Astra) are optimized for immediate task completion and localized unit-test passing. When given an engineering task that conflicts with existing class boundaries, models take the **path of least resistance**:
1. Appending conditional flags (`skip_validation=True`) to existing signatures.
2. Bloating existing domain classes with alien use-cases (`OrderService.process_internal_payment`).
3. Forcing existing schema constraints onto new domains (e.g., forcing corporate batch billing jobs to create dummy customer orders).

This benchmark evaluates whether an AI agent can recognize when an abstraction's boundary has been exceeded and apply disciplined architectural design principles (Single Responsibility Principle, Explicit Composition, Interface Segregation) rather than accumulating codebase bloat.

---

## 2. Failure Modes

### Failure Mode A: The "Boolean Bypass Flag" (Severity: High / Instant Fail)
- **Signature:** `def process_order(..., skip_validation: bool = False, is_internal: bool = False)`
- **Mechanism:** Inlines a conditional branch inside `process_order` to bypass checks.
- **Why it Fails:**
  - Turns fundamental domain invariants (active customer, pending order) into optional parameters.
  - Exposes an unsafe bypass flag to all external/customer call sites.
  - Multiplies branch complexity; over time, accumulates dozens of flags ("codebase bloat").

### Failure Mode B: The "Class-Bloat Bypass" (Severity: High / Architectural Fail)
- **Signature:** Appending `def process_internal_payment(...)` directly onto `OrderService`.
- **Mechanism:** The model avoids the boolean flag, but crams recurring enterprise billing into `OrderService`. It often extracts a shared helper (`_charge()`) inside `OrderService`.
- **Why it Fails:**
  - **Ownership Violation:** `OrderService` is the domain owner of customer orders. Enterprise subscription billing is not an order.
  - **Security / Boundary Leak:** Any caller that receives an `OrderService` instance (e.g., web API controllers, public checkout handlers) can now invoke `process_internal_payment` and bypass all customer status and order state gates. The bypass can only be contained at wiring time, yet the model exposes it on the customer service interface.
  - **Dead Dependencies:** Batch billing callers are forced to depend on `OrderService` which requires `notification_service`, even though receipts are never sent.

### Failure Mode C: The "Agent Over-Fitting / Schema Forcing" (Severity: Medium-High)
- **Observation:** When agents (e.g., Claude Code) generate unit tests, they optimize to make all tests green by forcing constraints onto the new caller:
  - e.g., requiring the internal billing caller to provide an `order_id` and querying `db.get_order()`, even though the requirement explicitly states internal batch jobs do not follow an order lifecycle!

---

## 3. The Passing Standard: Architectural Principle Adherence (PASS)

To pass, the implementation must demonstrate:

1. **Zero Customer Regression Risk:**
   - The existing `OrderService.process_order()` and its public contract must remain strictly preserved, with domain invariants intact. No customer-facing caller can bypass validation.

2. **Explicit Separation of Concerns & Clean Ownership:**
   - Either:
     - **Dedicated Service (Sibling Pattern):** Create an independent `InternalBillingService` (or `CorporateBillingService`) that accepts only the dependencies it requires (`db`, `payment_gateway`). It has zero dependency on `notification_service` and does not interact with `Order` records.
     - **Extracted Payment Core:** Proactively refactor low-level gateway interactions into a dedicated `PaymentProcessor`, leaving `OrderService` and `InternalBillingService` as peer consumers.

3. **Safe Composition Root Wiring:**
   - The internal payment capability is only exposed to trusted internal job workers via dependency injection at the composition root, completely isolated from customer checkout wiring.
