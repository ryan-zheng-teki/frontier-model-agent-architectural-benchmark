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
| **Claude Sonnet 5.5** (`xhigh`) | **FAIL** ([`claude-code-sonnet-5-5-xhigh`](experiments/claude-code-sonnet-5-5-xhigh/))<br>• Added `process_internal_payment` to `OrderService`<br>• Conceded stronger architectural option is "move to separate `InternalBillingService`", but kept on `OrderService`<br>• Leaked bypass to customer wiring | **PASS** ([`autobyteus-sonnet-5-5-xhigh`](experiments/autobyteus-sonnet-5-5-xhigh/))<br>• Created separate class `EnterpriseBillingService`<br>• Strict DI (`db`, `payment_gateway` only)<br>• Factored `_charge_or_raise` helper<br>• 17 unit/boundary tests + 6-stage lifecycle reports | Same model: under Claude Code it bloated `OrderService` with an unvetted method; under AutoByteus it cleanly separated `EnterpriseBillingService` with strict DI and 17 tests. |
| **Claude Opus 5.5** (`xhigh`) | **FAIL** ([`claude-code-opus-5-5-xhigh`](experiments/claude-code-opus-5-5-xhigh/))<br>• Added `process_internal_payment` to `OrderService`<br>• Acknowledged separate service offers "cleaner isolation" but chose class bloat ("not worth it yet")<br>• Forces `order = db.get_order()` (crashes if no order)<br>• Leaked bypass to customer wiring | **FAIL** ([`autobyteus-opus-5-5-xhigh`](experiments/autobyteus-opus-5-5-xhigh/evaluation.md))<br>• Full 6-stage lifecycle (15 tests, PASS)<br>• Rejected boolean flags (PASS)<br>• Added `process_internal_enterprise_payment` on `OrderService` (Class Bloat)<br>• Forced `order = db.get_order()` & `order.status = PAID` (Schema Forcing)<br>• Echo chamber: reviewer approved bloat | Across both Claude Code and AutoByteus, Opus 5.5 persistently defended Class Bloat and Schema Forcing, explicitly arguing in `DESIGN.md` that a separate service class is "disproportionate." AutoByteus provided full process governance, but the homogeneous reviewer persona rubber-stamped the model's anti-abstraction bias. |
| **Gemini 3.8** (`high`) | **FAIL** ([`agy-gemini-3-8-high`](experiments/agy-gemini-3-8-high/))<br>• Added `is_internal: bool = False` flag to `process_order`<br>• Inlined `if not is_internal:` bypass checks<br>• Forces `order = db.get_order()` (crashes if no order)<br>• Defended as "minimal code surface" | *(In Progress)* ([`autobyteus-gemini-3-8-high`](experiments/autobyteus-gemini-3-8-high/))<br>Testing via AutoByteus Runtime | In an unpolluted sandbox, Gemini 3.8 took the path of least resistance: adding a boolean bypass flag, claiming to avoid "premature abstractions", and leaking the bypass to public routes. |
| **OpenAI Astra** (`xhigh`) | **FAIL** ([`codex-astra-xhigh`](experiments/codex-astra-xhigh/))<br>• Added `process_payment(token, amount)` to `OrderService`<br>• Turned `OrderService` into generic payment gateway proxy<br>• Pollutes constructor (callers must inject unused `db` and `notification_service`)<br>• Public security bypass on order domain | **PASS** ([`autobyteus-astra-xhigh`](experiments/autobyteus-astra-xhigh/))<br>• Added `process_payment(token, amount)`<br>• 0 Schema Forcing (no order dependency)<br>• Guarded by `UnusableDependency` tests<br>• Full 6-stage lifecycle & delivery receipt | Under Codex CLI, Astra ran single-file without lifecycle checks; under AutoByteus it completed the full 6-stage lifecycle and enforced dependency isolation with `UnusableDependency`. |
| **OpenAI Sol 6.1** (`xhigh`) | **FAIL** ([`codex-sol-6-1-xhigh`](experiments/codex-sol-6-1-xhigh/))<br>• Added `process_internal_order` to `OrderService`<br>• Forces `order = db.get_order()` (crashes if no order)<br>• Forces `order.status = "PAID"` & `db.save_order()`<br>• Pollutes constructor with `notification_service` | **PASS** ([`autobyteus-sol-6-1-xhigh`](experiments/autobyteus-sol-6-1-xhigh/))<br>• Added `process_payment(token, amount)`<br>• 0 Schema Forcing (no order dependency)<br>• Passed Architecture Review & Code Review (100/100)<br>• Enforced by `ForbiddenDependency` tests | Same model: under Codex CLI it forced dummy orders and bloated `OrderService`; under AutoByteus it authored a rigorous design spec, eliminated Schema Forcing, and verified isolation with `ForbiddenDependency`. |

---

## 4. Key Empirical Findings & Model Case Studies

For the complete architectural taxonomy and failure mode analysis, read **[`BENCHMARK_RESULTS.md`](BENCHMARK_RESULTS.md)**.

### Case 1: The "All 16 Unit Tests Pass" Mirage (Claude Sonnet 5.5 under Claude Code)
When running Claude Code on this task, the agent celebrated: *"All 16 unit tests pass."* However, inspection revealed that to get 16 tests green inside `OrderService`, the agent:
- Forced corporate batch jobs to check `db.get_order()`, directly contradicting the requirement that batch jobs do not have an order lifecycle.
- Conceded in its design notes: *"Real protection means never exposing this method through a customer-facing route"*—yet placed it directly on the customer-facing `OrderService`!
- Under **AutoByteus**, Sonnet 5.5 cleanly decoupled into `EnterpriseBillingService` with strict DI (`db`, `payment_gateway` only) and 17 unit/boundary tests.

### Case 2: Invariant Guard Tests (OpenAI Sol 6.1 & Astra under AutoByteus)
Under Codex CLI, both Sol 6.1 and Astra fell into Class Bloat and Schema Forcing. Under AutoByteus, both models extracted a pure `process_payment(payment_token, amount)` contract with zero order dependencies, and mathematically enforced isolation using poison-pill mocks (`ForbiddenDependency` / `UnusableDependency`) that fail on any database or notification access.

### Case 3: The Persistent Anti-Abstraction Bias (Claude Opus 5.5)
Both under Claude Code and under AutoByteus, Opus 5.5 persistently defended keeping the method on `OrderService` and forcing `order = db.get_order()`. In `DESIGN.md`, it argued that creating a separate service class is "disproportionate." Because both the Solution Designer and Architecture Reviewer ran Opus 5.5, the reviewer rubber-stamped this decision—revealing the risk of **homogeneous reviewer echo chambers**.

---

## 5. Repository Structure

```text
├── README.md                                  # Benchmark overview, empirical findings, and thesis
├── BENCHMARK_RESULTS.md                       # Comprehensive architectural report & failure taxonomy
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
    ├── autobyteus-gemini-3-8-high/            # Ready for Gemini 3.8 AutoByteus run
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
