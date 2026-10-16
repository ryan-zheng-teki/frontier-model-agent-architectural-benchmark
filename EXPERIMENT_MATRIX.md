# Benchmark Experiment Matrix: Frontier Models × Harnesses

**Benchmark Task:** [`TASK.md`](TASK.md) (OrderService Internal Enterprise Billing)

**Evaluation Setup:**
- Frontier models evaluated with high reasoning budget (`thinking: xhigh` / `thinking: high`).
- Tested across two execution environments:
  1. **Vendor Native / Agent Harness:** (Anthropic Claude Code, OpenAI Codex CLI, Antigravity AGY).
  2. **AutoByteus Runtime:** Autonomous principle-guided runtime with explicit architectural design principles, domain boundary enforcement, and solution review gates.

---

## The 2D Comparison Matrix

| Model & Reasoning | Agent Harness | AutoByteus Runtime | Architectural Delta & Insight |
| :--- | :--- | :--- | :--- |
| **Claude Sonnet 5.5** (`xhigh`) | **FAIL** ([`claude-code-sonnet-5-5-xhigh`](experiments/claude-code-sonnet-5-5-xhigh/))<br>• Added `process_internal_payment` to `OrderService`<br>• Conceded stronger architectural option is "move to separate `InternalBillingService`", but kept on `OrderService`<br>• Leaked bypass to customer wiring | **PASS** ([`autobyteus-sonnet-5-5-xhigh`](experiments/autobyteus-sonnet-5-5-xhigh/))<br>• Created separate class `EnterpriseBillingService`<br>• Strict DI (`db`, `payment_gateway` only)<br>• Factored `_charge_or_raise` helper<br>• 17 unit/boundary tests + 6-stage lifecycle reports | Same model: under Claude Code it bloated `OrderService` with an unvetted method; under AutoByteus it cleanly separated `EnterpriseBillingService` with strict DI and 17 tests. |
| **Claude Opus 5.5** (`xhigh`) | **FAIL** ([`claude-code-opus-5-5-xhigh`](experiments/claude-code-opus-5-5-xhigh/))<br>• Added `process_internal_payment` to `OrderService`<br>• Acknowledged separate service offers "cleaner isolation" but chose class bloat ("not worth it yet")<br>• Forces `order = db.get_order()` (crashes if no order)<br>• Leaked bypass to customer wiring | **FAIL** ([`autobyteus-opus-5-5-xhigh`](experiments/autobyteus-opus-5-5-xhigh/evaluation.md))<br>• Full 6-stage lifecycle (15 tests, PASS)<br>• Rejected boolean flags (PASS)<br>• Added `process_internal_enterprise_payment` on `OrderService` (Class Bloat)<br>• Forced `order = db.get_order()` & `order.status = PAID` (Schema Forcing)<br>• Echo chamber: reviewer approved bloat | Across both Claude Code and AutoByteus, Opus 5.5 persistently defended Class Bloat and Schema Forcing, explicitly arguing in `DESIGN.md` that a separate service class is "disproportionate." AutoByteus provided full process governance, but the homogeneous reviewer persona rubber-stamped the model's anti-abstraction bias. |
| **Gemini 3.8** (`high`) | **FAIL** ([`agy-gemini-3-8-high`](experiments/agy-gemini-3-8-high/))<br>• Added `is_internal: bool = False` flag to `process_order`<br>• Inlined `if not is_internal:` bypass checks<br>• Forces `order = db.get_order()` (crashes if no order)<br>• Defended as "minimal code surface" | *(In Progress)* ([`autobyteus-gemini-3-8-high`](experiments/autobyteus-gemini-3-8-high/))<br>Testing via AutoByteus Runtime | In an unpolluted sandbox, Gemini 3.8 took the path of least resistance: adding a boolean bypass flag, claiming to avoid "premature abstractions", and leaking the bypass to public routes. |
| **Gemini 4 Argon** | *(Ready for Testing)* ([`agy-gemini-4-argon`](experiments/agy-gemini-4-argon/)) | *(Ready for Testing)* ([`autobyteus-gemini-4-argon`](experiments/autobyteus-gemini-4-argon/)) | Baselines staged in `experiments/agy-gemini-4-argon/` and `experiments/autobyteus-gemini-4-argon/`. Ready for execution. |
| **OpenAI Astra** (`xhigh`) | **FAIL** ([`codex-astra-xhigh`](experiments/codex-astra-xhigh/))<br>• Added `process_payment(token, amount)` to `OrderService`<br>• Turned `OrderService` into generic payment gateway proxy<br>• Pollutes constructor (callers must inject unused `db` and `notification_service`)<br>• Public security bypass on order domain | **PASS** ([`autobyteus-astra-xhigh`](experiments/autobyteus-astra-xhigh/))<br>• Added `process_payment(token, amount)`<br>• 0 Schema Forcing (no order dependency)<br>• Guarded by `UnusableDependency` tests<br>• Full 6-stage lifecycle & delivery receipt | Under Codex CLI, Astra ran single-file without lifecycle checks; under AutoByteus it completed the full 6-stage lifecycle and enforced dependency isolation with `UnusableDependency`. |
| **OpenAI Sol 6.1** (`xhigh`) | **FAIL** ([`codex-sol-6-1-xhigh`](experiments/codex-sol-6-1-xhigh/))<br>• Added `process_internal_order` to `OrderService`<br>• Forces `order = db.get_order()` (crashes if no order)<br>• Forces `order.status = "PAID"` & `db.save_order()`<br>• Pollutes constructor with `notification_service` | **PASS** ([`autobyteus-sol-6-1-xhigh`](experiments/autobyteus-sol-6-1-xhigh/))<br>• Added `process_payment(token, amount)`<br>• 0 Schema Forcing (no order dependency)<br>• Passed Architecture Review & Code Review (100/100)<br>• Enforced by `ForbiddenDependency` tests | Same model: under Codex CLI it forced dummy orders and bloated `OrderService`; under AutoByteus it authored a rigorous design spec, eliminated Schema Forcing, and verified isolation with `ForbiddenDependency`. |

---

## Directory Organization & Evidence Index

For the full architectural write-up, failure mode taxonomy, and case studies, see **[`BENCHMARK_RESULTS.md`](BENCHMARK_RESULTS.md)**.

```text
experiments/
├── claude-code-sonnet-5-5-xhigh/              # Claude Code (16 passing tests & class bloat)
│   ├── run-trace.md
│   ├── direct-prompt-response.md
│   ├── order_service.py
│   ├── DESIGN.md
│   └── evaluation.md
├── autobyteus-sonnet-5-5-xhigh/               # AutoByteus Solution Designer (SR-002 PASS)
│   ├── order_service.py (baseline untouched)
│   ├── internal_billing_service.py (clean separate class)
│   ├── DESIGN.md
│   ├── evaluation.md
│   └── solution-package/                     # Full 6-stage lifecycle tickets & tests
│
├── claude-code-opus-5-5-xhigh/                # Claude Code (Class bloat & schema forcing)
│   ├── order_service.py
│   ├── DESIGN.md
│   └── evaluation.md
├── autobyteus-opus-5-5-xhigh/                 # AutoByteus Runtime (Lifecycle PASS, Architecture FAIL)
│   ├── order_service.py (bloated process_internal_enterprise_payment)
│   ├── DESIGN.md (explicit defense of class bloat)
│   ├── test_order_service.py (15 passing tests asserting order_id shape)
│   ├── evaluation.md
│   └── tickets/done/internal-enterprise-payment/ # Full 6-stage lifecycle
│
├── agy-gemini-3-8-high/                       # Antigravity AGY (Boolean flag bypass)
│   ├── order_service.py (inlined is_internal flag)
│   ├── DESIGN.md
│   └── evaluation.md
├── autobyteus-gemini-3-8-high/                # Ready for Gemini 3.8 AutoByteus run
│   ├── order_service.py (baseline)
│   └── README.md
│
├── agy-gemini-4-argon/                        # Ready for Gemini 4 Argon Antigravity run
│   ├── order_service.py (baseline)
│   └── README.md
├── autobyteus-gemini-4-argon/                 # Ready for Gemini 4 Argon AutoByteus run
│   ├── order_service.py (baseline)
│   └── README.md
│
├── codex-astra-xhigh/                         # Codex CLI (Gateway proxy, constructor pollution)
│   ├── order_service.py
│   ├── DESIGN.md
│   └── evaluation.md
├── autobyteus-astra-xhigh/                    # AutoByteus Runtime (PASS)
│   ├── order_service.py (clean process_payment extraction)
│   ├── DESIGN.md
│   ├── test_order_service.py (UnusableDependency invariant guards)
│   ├── evaluation.md
│   └── tickets/done/internal-enterprise-payments/ # Full 6-stage lifecycle
│
├── codex-sol-6-1-xhigh/                       # Codex CLI (Class bloat & schema forcing)
│   ├── order_service.py
│   ├── DESIGN.md
│   └── evaluation.md
└── autobyteus-sol-6-1-xhigh/                  # AutoByteus Runtime (PASS)
    ├── order_service.py (clean process_payment extraction)
    ├── DESIGN.md
    ├── test_order_service.py (ForbiddenDependency invariant guards)
    ├── evaluation.md
    └── solution/                              # Full 6-stage lifecycle
```
