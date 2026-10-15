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
| **Claude Sonnet 5.5** (`xhigh`) | **FAIL** ([`claude-code-sonnet-5-5-xhigh`](experiments/claude-code-sonnet-5-5-xhigh/))<br>• Crammed batch billing into `OrderService`<br>• "All 16 unit tests pass"<br>• Forced dummy order checks onto batch jobs<br>• Leaked bypass to customer wiring | **PASS** ([`autobyteus-sonnet-5-5-xhigh`](experiments/autobyteus-sonnet-5-5-xhigh/))<br>• `order_service.py` untouched (0 regression)<br>• Created `InternalBillingService`<br>• Isolated at composition root<br>• No order dependency | **Same model, opposite architecture.** Proves that current agent harnesses incentivize test-hacking and class bloat over system health. |
| **Claude Opus 5.5** (`xhigh`) | *(In Progress)* ([`claude-code-opus-5-5-xhigh`](experiments/claude-code-opus-5-5-xhigh/))<br>Testing via Claude Code with `xhigh` | *(In Progress)* ([`autobyteus-opus-5-5-xhigh`](experiments/autobyteus-opus-5-5-xhigh/))<br>Testing via AutoByteus Runtime | Testing if increased raw model capacity alone overcomes the class-bloat trap without principle-guided runtime rules. |
| **Gemini 3.8** (`high`) | *(In Progress)* ([`agy-gemini-3-8-high`](experiments/agy-gemini-3-8-high/))<br>Testing via Antigravity (AGY) with `high` | *(In Progress)* ([`autobyteus-gemini-3-8-high`](experiments/autobyteus-gemini-3-8-high/))<br>Testing via AutoByteus Runtime | Directly relevant to Google DeepMind Polaris evaluation-to-training feedback loop. |
| **OpenAI Sol 6.1** (`xhigh`) | *(In Progress)* ([`codex-sol-6-1-xhigh`](experiments/codex-sol-6-1-xhigh/))<br>Testing via Codex CLI with `xhigh` | *(In Progress)* ([`autobyteus-sol-6-1-xhigh`](experiments/autobyteus-sol-6-1-xhigh/))<br>Testing via AutoByteus Runtime | Evaluating OpenAI's flagship reasoning model against boundary leakage. |

---

## Directory Organization

```text
experiments/
├── claude-code-sonnet-5-5-xhigh/              # Claude Code (16 passing tests & class bloat)
│   ├── run-trace.md
│   ├── direct-prompt-response.md
│   ├── order_service.py
│   └── evaluation.md
├── autobyteus-sonnet-5-5-xhigh/               # AutoByteus Solution Designer (SR-002)
│   ├── DESIGN.md
│   ├── internal_billing_service.py
│   └── evaluation.md
│
├── claude-code-opus-5-5-xhigh/                # Ready for Opus 5.5 Claude Code run
│   └── README.md
├── autobyteus-opus-5-5-xhigh/                 # Ready for Opus 5.5 AutoByteus run
│   └── README.md
│
├── agy-gemini-3-8-high/                       # Ready for Gemini 3.8 Antigravity (AGY) run
│   └── README.md
├── autobyteus-gemini-3-8-high/                # Ready for Gemini 3.8 AutoByteus run
│   └── README.md
│
├── codex-sol-6-1-xhigh/                       # Ready for Sol 6.1 Codex CLI run
│   └── README.md
└── autobyteus-sol-6-1-xhigh/                  # Ready for Sol 6.1 AutoByteus run
    └── README.md
```
