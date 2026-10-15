# Frontier AI Agent Architectural Benchmark

> **Empirical Evaluation of Frontier Models (`thinking: xhigh`) Across Vendor Native Harnesses vs. Principle-Guided AutoByteus Runtime.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 1. Thesis: The Test-Passing Evaluation Gap

Current frontier models (Sonnet 5.5, Opus 5.5, Sol 6.1, Astra / Gemini) excel at writing algorithms and getting unit tests to pass (`pytest == 0`). However, when deployed on real-world production codebases, engineering teams report a widespread systemic failure: **severe codebase bloat, architectural decay, and spaghetti code**.

Why does this happen?

**The Root Cause:**
Coding benchmarks (SWE-bench, HumanEval) evaluate agents solely on **immediate task completion and localized test passing**. Because models are intensely goal-oriented to satisfy the test harness as quickly as possible with minimal diffs, they consistently take the **path of least resistance**:
1. Appending conditional flags (`skip_validation=True`) to existing signatures.
2. Bloating existing domain classes with alien use-cases (`OrderService.process_internal_payment`).
3. Forcing existing schema constraints onto new domains (e.g., forcing corporate batch billing jobs to create dummy customer orders).

In real software engineering, solving a problem is a disciplined journey where one must adhere to core design principles (Single Responsibility Principle, clear data ownership, explicit boundaries) **while** reaching the solution. Current evaluations lack signals for architectural discipline, which means models are never trained to resist the path of least resistance.

This benchmark provides a simple, reproducible empirical test that exposes this gap across frontier models.

---

## 2. Experimental Setup: 2D Matrix (Models × Harnesses)

All models are evaluated using **maximum reasoning depth (`thinking: xhigh`)** across two execution environments:
1. **Vendor Native Harness:** The vendor's official agent harness (Anthropic Claude Code, OpenAI Codex CLI, Google Gemini CLI / AI Studio).
2. **AutoByteus Runtime:** Autonomous principle-guided runtime with explicit architectural design principles, domain boundary enforcement, and solution review gates.

### Tested Models
- **Anthropic Claude Sonnet 5.5** (`thinking: xhigh`)
- **Anthropic Claude Opus 5.5** (`thinking: xhigh`)
- **Google Astra / Gemini** (`thinking: xhigh`)
- **OpenAI Sol 6.1** (`thinking: xhigh`)

---

## 3. The 2D Comparison Matrix

See [`EXPERIMENT_MATRIX.md`](EXPERIMENT_MATRIX.md) for full details.

| Model (`thinking: xhigh`) | Vendor Native Harness | AutoByteus Runtime | Architectural Delta & Insight |
| :--- | :--- | :--- | :--- |
| **Claude Sonnet 5.5** | **FAIL**<br>• Crammed batch billing into `OrderService`<br>• "All 16 unit tests pass"<br>• Forced dummy order checks onto batch jobs<br>• Leaked bypass to customer wiring | **PASS**<br>• `order_service.py` untouched (0 regression)<br>• Created `InternalBillingService`<br>• Isolated at composition root<br>• No order dependency | **Same model, opposite architecture.** Proves that current agent harnesses incentivize test-hacking and class bloat over system health. |
| **Claude Opus 5.5** | *(In Progress)*<br>Testing via Claude Code with `xhigh` | *(In Progress)*<br>Testing via AutoByteus Runtime | Testing if increased raw model capacity alone overcomes the class-bloat trap without principle-guided runtime rules. |
| **Google Astra / Gemini** | *(In Progress)*<br>Testing via Google Native Harness with `xhigh` | *(In Progress)*<br>Testing via AutoByteus Runtime | Directly relevant to Google DeepMind Polaris evaluation-to-training feedback loop. |
| **OpenAI Sol 6.1** | *(In Progress)*<br>Testing via Codex CLI with `xhigh` | *(In Progress)*<br>Testing via AutoByteus Runtime | Evaluating OpenAI's flagship reasoning model against boundary leakage. |

---

## 4. Key Empirical Findings (Sonnet 5.5 Case Study)

### 1. The "All 16 Unit Tests Pass" Mirage (Claude Code)
When running Claude Code on this task, the agent celebrated: *"All 16 unit tests pass."*
However, inspection revealed that to get 16 tests green inside `OrderService`, the agent:
- Forced corporate batch jobs to check `db.get_order()`, directly contradicting the requirement that batch jobs do not have an order lifecycle.
- Conceded in its design notes: *"Real protection means never exposing this method through a customer-facing route"*—yet placed it directly on the customer-facing `OrderService`!

### 2. The Class-Bloat Trap (Claude Sonnet)
Both Claude Sonnet and Claude Code knew not to add a boolean flag (`skip_validation=True`), but both fell into the **Class-Bloat Trap**. Because their objective function penalizes cross-file refactoring and diff size, they kept everything inside `OrderService`, polluting the retail order domain with batch billing logic.

### 3. The Power of Principle-Guided Design (AutoByteus Runtime)
By enforcing architectural rules (Single Responsibility Principle, zero customer regression risk, and explicit composition roots), the AutoByteus Runtime:
- Recognized that `OrderService` and enterprise billing have orthogonal lifecycles and dependencies.
- Refused to touch `order_service.py`, guaranteeing zero customer regression.
- Created an independent, minimal `InternalBillingService` with only `db` and `payment_gateway` dependencies.

---

## 5. Repository Structure

```text
├── README.md                                  # Benchmark overview, empirical findings, and thesis
├── EXPERIMENT_MATRIX.md                       # Comprehensive 2D scorecard
├── LICENSE                                    # MIT License
├── .gitignore
├── benchmark/
│   ├── README.md                              # Task summary and hypotheses
│   ├── prompt.md                              # Exact copy-paste prompt for models
│   ├── order_service_baseline.py              # Baseline production code
│   └── rubric.md                              # Detailed grading rubric
└── experiments/
    ├── sonnet-5.5-xhigh/
    │   ├── README.md
    │   ├── native-harness/                    # Claude Code run
    │   └── autobyteus-runtime/                # AutoByteus Solution Designer
    ├── opus-5.5-xhigh/
    │   ├── README.md
    │   ├── native-harness/
    │   └── autobyteus-runtime/
    ├── astra-gemini-xhigh/
    │   ├── README.md
    │   ├── native-harness/
    │   └── autobyteus-runtime/
    └── sol-6.1-xhigh/
        ├── README.md
        ├── native-harness/
        └── autobyteus-runtime/
```

---

## 6. How to Reproduce

1. Copy the prompt from [`benchmark/prompt.md`](benchmark/prompt.md).
2. Paste into any frontier model or coding agent in a clean session with `thinking: xhigh`.
3. Compare the generated solution against [`benchmark/rubric.md`](benchmark/rubric.md).
4. Check whether the model:
   - Added a boolean flag (Level 1 Fail).
   - Bloated `OrderService` with internal batch methods (Level 2 Fail).
   - Forced dummy order checks onto batch jobs to pass tests (Level 3 Fail).
   - Or cleanly separated concerns into a dedicated service (Pass).
