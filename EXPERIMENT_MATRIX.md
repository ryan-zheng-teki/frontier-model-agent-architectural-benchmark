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
| **Claude Sonnet 5.5** (`xhigh`) | *(In Progress)* ([`claude-code-sonnet-5-5-xhigh`](experiments/claude-code-sonnet-5-5-xhigh/))<br>Testing via Claude Code with `xhigh` | **PASS** ([`autobyteus-sonnet-5-5-xhigh`](experiments/autobyteus-sonnet-5-5-xhigh/))<br>• `order_service.py` untouched (0 regression)<br>• Created `InternalBillingService`<br>• Isolated at composition root<br>• No order dependency | Comparing Claude Code native harness against AutoByteus principle-guided runtime. |
| **Claude Opus 5.5** (`xhigh`) | *(In Progress)* ([`claude-code-opus-5-5-xhigh`](experiments/claude-code-opus-5-5-xhigh/))<br>Testing via Claude Code with `xhigh` | *(In Progress)* ([`autobyteus-opus-5-5-xhigh`](experiments/autobyteus-opus-5-5-xhigh/))<br>Testing via AutoByteus Runtime | Testing if increased raw model capacity alone overcomes the class-bloat trap without principle-guided runtime rules. |
| **Gemini 3.8** (`high`) | **FAIL** ([`agy-gemini-3-8-high`](experiments/agy-gemini-3-8-high/))<br>• Added `is_internal: bool = False` flag to `process_order`<br>• Inlined `if not is_internal:` bypass checks<br>• Forces `order = db.get_order()` (crashes if no order)<br>• Defended as "minimal code surface" | *(In Progress)* ([`autobyteus-gemini-3-8-high`](experiments/autobyteus-gemini-3-8-high/))<br>Testing via AutoByteus Runtime | In an unpolluted sandbox, Gemini 3.8 took the path of least resistance: adding a boolean bypass flag, claiming to avoid "premature abstractions", and leaking the bypass to public routes. |
| **OpenAI Astra** (`xhigh`) | *(In Progress)* ([`codex-astra-xhigh`](experiments/codex-astra-xhigh/))<br>Testing via Codex CLI with `xhigh` | *(In Progress)* ([`autobyteus-astra-xhigh`](experiments/autobyteus-astra-xhigh/))<br>Testing via AutoByteus Runtime | Evaluating OpenAI Astra flagship model under maximum thinking budget. |
| **OpenAI Sol 6.1** (`xhigh`) | *(In Progress)* ([`codex-sol-6-1-xhigh`](experiments/codex-sol-6-1-xhigh/))<br>Testing via Codex CLI with `xhigh` | *(In Progress)* ([`autobyteus-sol-6-1-xhigh`](experiments/autobyteus-sol-6-1-xhigh/))<br>Testing via AutoByteus Runtime | Evaluating OpenAI Sol 6.1 flagship model against boundary leakage. |

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
