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
| **Claude Sonnet 5.5** (`xhigh`) | **FAIL** ([`claude-code-sonnet-5-5-xhigh`](experiments/claude-code-sonnet-5-5-xhigh/))<br>• Added `process_internal_payment` to `OrderService`<br>• Conceded stronger architectural option is "move to separate `InternalBillingService`", but kept on `OrderService`<br>• Leaked bypass to customer wiring | **PASS** ([`autobyteus-sonnet-5-5-xhigh`](experiments/autobyteus-sonnet-5-5-xhigh/))<br>• `order_service.py` untouched (0 regression)<br>• Created `InternalBillingService`<br>• Isolated at composition root<br>• No order dependency | Same model: under Claude Code it bloated `OrderService` while admitting a separate service is stronger; under AutoByteus it cleanly created `InternalBillingService`. |
| **Claude Opus 5.5** (`xhigh`) | **FAIL** ([`claude-code-opus-5-5-xhigh`](experiments/claude-code-opus-5-5-xhigh/))<br>• Added `process_internal_payment` to `OrderService`<br>• Acknowledged separate service offers "cleaner isolation" but chose class bloat ("not worth it yet")<br>• Forces `order = db.get_order()` (crashes if no order)<br>• Leaked bypass to customer wiring | *(In Progress)* ([`autobyteus-opus-5-5-xhigh`](experiments/autobyteus-opus-5-5-xhigh/))<br>Testing via AutoByteus Runtime | Opus 5.5 explicitly identified that a separate `InternalBillingService` is "cleaner isolation", but consciously chose class bloat to avoid file/wiring overhead. |
| **Gemini 3.8** (`high`) | **FAIL** ([`agy-gemini-3-8-high`](experiments/agy-gemini-3-8-high/))<br>• Added `is_internal: bool = False` flag to `process_order`<br>• Inlined `if not is_internal:` bypass checks<br>• Forces `order = db.get_order()` (crashes if no order)<br>• Defended as "minimal code surface" | *(In Progress)* ([`autobyteus-gemini-3-8-high`](experiments/autobyteus-gemini-3-8-high/))<br>Testing via AutoByteus Runtime | In an unpolluted sandbox, Gemini 3.8 took the path of least resistance: adding a boolean bypass flag, claiming to avoid "premature abstractions", and leaking the bypass to public routes. |
| **OpenAI Astra** (`xhigh`) | **FAIL** ([`codex-astra-xhigh`](experiments/codex-astra-xhigh/))<br>• Added `process_payment(token, amount)` to `OrderService`<br>• Turned `OrderService` into generic payment gateway proxy<br>• Pollutes constructor (callers must inject unused `db` and `notification_service`)<br>• Public security bypass on order domain | *(In Progress)* ([`autobyteus-astra-xhigh`](experiments/autobyteus-astra-xhigh/))<br>Testing via AutoByteus Runtime | Under Codex CLI, Astra avoided boolean flags and forced order queries, but bloated `OrderService` into a payment proxy, forcing callers to inject unneeded dependencies. |
| **OpenAI Sol 6.1** (`xhigh`) | **FAIL** ([`codex-sol-6-1-xhigh`](experiments/codex-sol-6-1-xhigh/))<br>• Added `process_internal_order` to `OrderService`<br>• Forces `order = db.get_order()` (crashes if no order)<br>• Forces `order.status = "PAID"` & `db.save_order()`<br>• Pollutes constructor with `notification_service` | *(In Progress)* ([`autobyteus-sol-6-1-xhigh`](experiments/autobyteus-sol-6-1-xhigh/))<br>Testing via AutoByteus Runtime | Sol 6.1 bloated `OrderService` and committed Schema Forcing: forced batch recurring billing to query and save an Order entity, crashing if no order exists. |

---

## Directory Organization

```text
experiments/
├── claude-code-sonnet-5-5-xhigh/              # Claude Code (16 passing tests & class bloat)
│   ├── run-trace.md
│   ├── direct-prompt-response.md
│   ├── order_service.py
│   ├── DESIGN.md
│   └── evaluation.md
├── autobyteus-sonnet-5-5-xhigh/               # AutoByteus Solution Designer (SR-002)
│   ├── order_service.py (baseline untouched)
│   ├── internal_billing_service.py (new service)
│   ├── DESIGN.md
│   └── evaluation.md
│
├── claude-code-opus-5-5-xhigh/                # Ready for Opus 5.5 Claude Code run
│   ├── order_service.py (baseline)
│   └── README.md
├── autobyteus-opus-5-5-xhigh/                 # Ready for Opus 5.5 AutoByteus run
│   ├── order_service.py (baseline)
│   └── README.md
│
├── agy-gemini-3-8-high/                       # Ready for Gemini 3.8 Antigravity (AGY) run
│   ├── order_service.py (baseline)
│   └── README.md
├── autobyteus-gemini-3-8-high/                # Ready for Gemini 3.8 AutoByteus run
│   ├── order_service.py (baseline)
│   └── README.md
│
├── codex-astra-xhigh/                         # Ready for Astra Codex CLI run
│   ├── order_service.py (baseline)
│   └── README.md
├── autobyteus-astra-xhigh/                    # Ready for Astra AutoByteus run
│   ├── order_service.py (baseline)
│   └── README.md
│
├── codex-sol-6-1-xhigh/                       # Ready for Sol 6.1 Codex CLI run
│   ├── order_service.py (baseline)
│   └── README.md
└── autobyteus-sol-6-1-xhigh/                  # Ready for Sol 6.1 AutoByteus run
    ├── order_service.py (baseline)
    └── README.md
```
