# Frontier AI Agent Architectural Benchmark

> **Empirical Evaluation of Frontier Coding Models on Architectural Invariants, Separation of Concerns, and Codebase Bloat.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 1. Thesis: The Test-Passing Evaluation Gap

Current frontier models (Sonnet 3.5/3.7, GPT-4o, o1, Gemini) excel at writing algorithms and getting unit tests to pass (`pytest == 0`). However, when deployed on real-world production codebases, engineering teams report a widespread systemic failure: **severe codebase bloat, architectural decay, and spaghetti code**.

Why does this happen?

**The Root Cause:**
Coding benchmarks (SWE-bench, HumanEval) evaluate agents solely on **immediate task completion and localized test passing**. Because models are intensely goal-oriented to satisfy the test harness as quickly as possible with minimal diffs, they consistently take the **path of least resistance**:
1. Appending conditional flags (`skip_validation=True`) to existing signatures.
2. Bloating existing domain classes with alien use-cases (`OrderService.process_internal_payment`).
3. Forcing existing schema constraints onto new domains (e.g., forcing corporate batch billing jobs to create dummy customer orders).

In real software engineering, solving a problem is a disciplined journey where one must adhere to core design principles (Single Responsibility Principle, clear data ownership, explicit boundaries) **while** reaching the solution. Current evaluations lack signals for architectural discipline, which means models are never trained to resist the path of least resistance.

This benchmark provides a simple, reproducible empirical test that exposes this gap across frontier models.

---

## 2. The Benchmark Task: `OrderService` Internal Enterprise Billing

### The Baseline Code
An `OrderService` manages the customer retail checkout lifecycle:
`Validation` -> `Order State Check` -> `Payment Gateway Charge` -> `Order Status Persistence (PAID)` -> `Customer Receipt Notification`.

### The Requirement
Internal recurring subscription billing jobs and administrative batch tasks need to charge pre-verified corporate enterprise accounts. These internal callers handle validation upstream and **do not follow the customer order lifecycle**. They need to process payments via the payment gateway without customer checks, order checks, or receipt notifications.

---

## 3. Empirical Results Across Frontier Models

| Model / Agent | Approach Taken | Order Checks | Boundary Safety | Result |
| :--- | :--- | :--- | :--- | :--- |
| **Claude Sonnet** (Direct Prompt) | Added `process_internal_payment` to `OrderService` | Skipped | Leaked to customer wiring | **FAIL** (Class Bloat) |
| **Claude Code** (Autonomous Agent) | Added `process_internal_payment` to `OrderService` ("All 16 unit tests pass") | **Forced dummy order checks** to pass tests | Leaked to customer wiring (admitted in rationale) | **FAIL** (Class Bloat & Schema Forcing) |
| **Google Gemini** | *(In Progress)* | TBD | TBD | Pending |
| **OpenAI Codex / Sol** | *(In Progress)* | TBD | TBD | Pending |
| **AutoByteus Solution Designer** (Principle-Guided) | Created standalone `InternalBillingService`, left `OrderService` untouched | Skipped (No order dependency) | Zero leak (isolated at composition root) | **PASS** (Zero Regression) |

---

## 4. Key Empirical Findings

### 1. The "All 16 Unit Tests Pass" Mirage (Claude Code)
When running Claude Code on this task, the agent celebrated: *"All 16 unit tests pass."*
However, inspection revealed that to get 16 tests green inside `OrderService`, the agent:
- Forced corporate batch jobs to check `db.get_order()`, directly contradicting the requirement that batch jobs do not have an order lifecycle.
- Conceded in its design notes: *"Real protection means never exposing this method through a customer-facing route"*—yet placed it directly on the customer-facing `OrderService`!

### 2. The Class-Bloat Trap (Claude Sonnet)
Both Claude Sonnet and Claude Code knew not to add a boolean flag (`skip_validation=True`), but both fell into the **Class-Bloat Trap**. Because their objective function penalizes cross-file refactoring and diff size, they kept everything inside `OrderService`, polluting the retail order domain with batch billing logic.

### 3. The Power of Principle-Guided Design (AutoByteus Solution Designer)
By enforcing architectural rules (Single Responsibility Principle, zero customer regression risk, and explicit composition roots), the AutoByteus Solution Designer:
- Recognized that `OrderService` and enterprise billing have orthogonal lifecycles and dependencies.
- Refused to touch `order_service.py`, guaranteeing zero customer regression.
- Created an independent, minimal `InternalBillingService` with only `db` and `payment_gateway` dependencies.

---

## 5. Repository Structure

```text
├── README.md                                  # Benchmark overview, empirical findings, and thesis
├── LICENSE                                    # MIT License
├── .gitignore
├── benchmark/
│   ├── README.md                              # Task summary and hypotheses
│   ├── prompt.md                              # Exact copy-paste prompt for models
│   ├── order_service_baseline.py              # Baseline production code
│   └── rubric.md                              # Detailed grading rubric
└── experiments/
    ├── claude-sonnet/                         # Claude Sonnet direct run & evaluation
    ├── claude-code/                           # Claude Code agent run & 16-test analysis
    ├── gemini/                                # Google Gemini run & evaluation
    ├── openai-codex/                          # OpenAI Codex / Sol run & evaluation
    └── autobyteus-solution-designer/          # AutoByteus principle-guided reference solution
```

---

## 6. How to Reproduce

1. Copy the prompt from [`benchmark/prompt.md`](benchmark/prompt.md).
2. Paste into any frontier model or coding agent in a clean session.
3. Compare the generated solution against [`benchmark/rubric.md`](benchmark/rubric.md).
4. Check whether the model:
   - Added a boolean flag (Level 1 Fail).
   - Bloated `OrderService` with internal batch methods (Level 2 Fail).
   - Forced dummy order checks onto batch jobs to pass tests (Level 3 Fail).
   - Or cleanly separated concerns into a dedicated service (Pass).
