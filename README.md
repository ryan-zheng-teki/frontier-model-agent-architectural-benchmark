# Frontier Model Agent Architectural Benchmark

> **Empirical Evaluation of Frontier Models Across Agent Harnesses (Claude Code, Codex CLI, Antigravity AGY) vs. Principle-Guided AutoByteus Runtime.**

[![GitHub Repo](https://img.shields.io/badge/GitHub-frontier--model--agent--architectural--benchmark-blue?logo=github)](https://github.com/ryan-zheng-teki/frontier-model-agent-architectural-benchmark)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 The Task: Copy & Run
The complete, copy-paste ready task prompt is available at **[`TASK.md`](TASK.md)**.
It presents an existing `OrderService` handling retail checkout, and introduces a requirement for internal batch enterprise billing with no order lifecycle.

---

## 1. Thesis: The Test-Passing Evaluation Gap

Current frontier models (Sonnet 5.5, Opus 5.5, Sol 6.1, Gemini 3.8, Astra) excel at writing algorithms and getting unit tests to pass (`pytest == 0`). However, when deployed on real-world production codebases, engineering teams report a widespread systemic failure: **severe codebase bloat, architectural decay, and spaghetti code**.

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

All models are evaluated using high reasoning budget across two execution environments:
1. **Agent Harness:** (Anthropic Claude Code, OpenAI Codex CLI, Antigravity AGY).
2. **AutoByteus Runtime:** Autonomous principle-guided runtime with explicit architectural design principles, domain boundary enforcement, and solution review gates.

### Tested Models
- **Anthropic Claude Sonnet 5.5** (`thinking: xhigh`)
- **Anthropic Claude Opus 5.5** (`thinking: xhigh`)
- **Google Gemini 3.8** (`thinking: high`)
- **OpenAI Astra** (`thinking: xhigh`)
- **OpenAI Sol 6.1** (`thinking: xhigh`)

---

## 3. The 2D Comparison Matrix

See [`EXPERIMENT_MATRIX.md`](EXPERIMENT_MATRIX.md) for full details.

| Model & Reasoning | Agent Harness | AutoByteus Runtime | Architectural Delta & Insight |
| :--- | :--- | :--- | :--- |
| **Claude Sonnet 5.5** (`xhigh`) | **FAIL** ([`claude-code-sonnet-5-5-xhigh`](experiments/claude-code-sonnet-5-5-xhigh/))<br>• Added `process_internal_payment` to `OrderService`<br>• Conceded stronger architectural option is "move to separate `InternalBillingService`", but kept on `OrderService`<br>• Leaked bypass to customer wiring | **PASS** ([`autobyteus-sonnet-5-5-xhigh`](experiments/autobyteus-sonnet-5-5-xhigh/))<br>• `order_service.py` untouched (0 regression)<br>• Created `InternalBillingService`<br>• Isolated at composition root<br>• No order dependency | Same model: under Claude Code it bloated `OrderService` while admitting a separate service is stronger; under AutoByteus it cleanly created `InternalBillingService`. |
| **Claude Opus 5.5** (`xhigh`) | **FAIL** ([`claude-code-opus-5-5-xhigh`](experiments/claude-code-opus-5-5-xhigh/))<br>• Added `process_internal_payment` to `OrderService`<br>• Acknowledged separate service offers "cleaner isolation" but chose class bloat ("not worth it yet")<br>• Forces `order = db.get_order()` (crashes if no order)<br>• Leaked bypass to customer wiring | *(In Progress)* ([`autobyteus-opus-5-5-xhigh`](experiments/autobyteus-opus-5-5-xhigh/))<br>Testing via AutoByteus Runtime | Opus 5.5 explicitly identified that a separate `InternalBillingService` is "cleaner isolation", but consciously chose class bloat to avoid file/wiring overhead. |
| **Gemini 3.8** (`high`) | **FAIL** ([`agy-gemini-3-8-high`](experiments/agy-gemini-3-8-high/))<br>• Added `is_internal: bool = False` flag to `process_order`<br>• Inlined `if not is_internal:` bypass checks<br>• Forces `order = db.get_order()` (crashes if no order)<br>• Defended as "minimal code surface" | *(In Progress)* ([`autobyteus-gemini-3-8-high`](experiments/autobyteus-gemini-3-8-high/))<br>Testing via AutoByteus Runtime | In an unpolluted sandbox, Gemini 3.8 took the path of least resistance: adding a boolean bypass flag, claiming to avoid "premature abstractions", and leaking the bypass to public routes. |
| **OpenAI Astra** (`xhigh`) | **FAIL** ([`codex-astra-xhigh`](experiments/codex-astra-xhigh/))<br>• Added `process_payment(token, amount)` to `OrderService`<br>• Turned `OrderService` into generic payment gateway proxy<br>• Pollutes constructor (callers must inject unused `db` and `notification_service`)<br>• Public security bypass on order domain | *(In Progress)* ([`autobyteus-astra-xhigh`](experiments/autobyteus-astra-xhigh/))<br>Testing via AutoByteus Runtime | Under Codex CLI, Astra avoided boolean flags and forced order queries, but bloated `OrderService` into a payment proxy, forcing callers to inject unneeded dependencies. |
| **OpenAI Sol 6.1** (`xhigh`) | **FAIL** ([`codex-sol-6-1-xhigh`](experiments/codex-sol-6-1-xhigh/))<br>• Added `process_internal_order` to `OrderService`<br>• Forces `order = db.get_order()` (crashes if no order)<br>• Forces `order.status = "PAID"` & `db.save_order()`<br>• Pollutes constructor with `notification_service` | *(In Progress)* ([`autobyteus-sol-6-1-xhigh`](experiments/autobyteus-sol-6-1-xhigh/))<br>Testing via AutoByteus Runtime | Sol 6.1 bloated `OrderService` and committed Schema Forcing: forced batch recurring billing to query and save an Order entity, crashing if no order exists. |

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
├── TASK.md                                    # Exact copy-paste prompt for models & agents
├── EXPERIMENT_MATRIX.md                       # Comprehensive 2D scorecard
├── LICENSE                                    # MIT License
├── .gitignore
├── benchmark/
│   ├── prompt.md                              # Benchmark task specification
│   ├── order_service.py                       # Baseline production code
│   └── rubric.md                              # Detailed grading rubric
└── experiments/
    ├── claude-code-sonnet-5-5-xhigh/          # Claude Code run (16 tests green, class bloat)
    ├── autobyteus-sonnet-5-5-xhigh/           # AutoByteus Solution Designer (SR-002 clean pass)
    ├── claude-code-opus-5-5-xhigh/            # Claude Code run with Opus 5.5
    ├── autobyteus-opus-5-5-xhigh/             # AutoByteus run with Opus 5.5
    ├── agy-gemini-3-8-high/                   # Antigravity (AGY) run with Gemini 3.8
    ├── autobyteus-gemini-3-8-high/            # AutoByteus run with Gemini 3.8
    ├── codex-astra-xhigh/                     # Codex CLI with Astra
    ├── autobyteus-astra-xhigh/                # AutoByteus run with Astra
    ├── codex-sol-6-1-xhigh/                   # Codex CLI with Sol 6.1
    └── autobyteus-sol-6-1-xhigh/              # AutoByteus run with Sol 6.1
```

---

## 6. How to Reproduce

1. Open [`TASK.md`](TASK.md) and copy the prompt.
2. Run in the target experiment directory with reasoning set to `high` / `xhigh`.
3. Compare the generated solution against [`benchmark/rubric.md`](benchmark/rubric.md).
4. Inspect code diffs via `git diff` and review the generated `DESIGN.md`.
