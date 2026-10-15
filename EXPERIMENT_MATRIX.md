# Benchmark Experiment Matrix: Frontier Models × Harnesses

**Benchmark Task:** [`TASK.md`](TASK.md) (OrderService Internal Enterprise Billing)

**Evaluation Setup:**
- All models evaluated with **`thinking: xhigh`** (maximum reasoning / chain-of-thought budget).
- Tested across two execution environments:
  1. **Vendor Native Harness:** The official autonomous coding agent / harness provided by the vendor (Anthropic Claude Code, OpenAI Codex CLI, Google Gemini CLI / AI Studio).
  2. **AutoByteus Runtime:** Autonomous principle-guided runtime with explicit architectural design principles, domain boundary enforcement, and solution review gates.

---

## The 2D Comparison Matrix

| Model (`thinking: xhigh`) | Vendor Native Harness | AutoByteus Runtime | Architectural Delta & Insight |
| :--- | :--- | :--- | :--- |
| **Claude Sonnet 5.5** | **FAIL** ([`claude-code-sonnet-5-5-xhigh`](experiments/claude-code-sonnet-5-5-xhigh/))<br>• Crammed batch billing into `OrderService`<br>• "All 16 unit tests pass"<br>• Forced dummy order checks onto batch jobs<br>• Leaked bypass to customer wiring | **PASS** ([`autobyteus-sonnet-5-5-xhigh`](experiments/autobyteus-sonnet-5-5-xhigh/))<br>• `order_service.py` untouched (0 regression)<br>• Created `InternalBillingService`<br>• Isolated at composition root<br>• No order dependency | **Same model, opposite architecture.** Proves that current agent harnesses incentivize test-hacking and class bloat over system health. |
| **Claude Opus 5.5** | *(In Progress)* ([`claude-code-opus-5-5-xhigh`](experiments/claude-code-opus-5-5-xhigh/))<br>Testing via Claude Code with `xhigh` | *(In Progress)* ([`autobyteus-opus-5-5-xhigh`](experiments/autobyteus-opus-5-5-xhigh/))<br>Testing via AutoByteus Runtime | Testing if increased raw model capacity alone overcomes the class-bloat trap without principle-guided runtime rules. |
| **Google Astra / Gemini** | *(In Progress)* ([`google-harness-astra-gemini-xhigh`](experiments/google-harness-astra-gemini-xhigh/))<br>Testing via Google Native Harness with `xhigh` | *(In Progress)* ([`autobyteus-astra-gemini-xhigh`](experiments/autobyteus-astra-gemini-xhigh/))<br>Testing via AutoByteus Runtime | Directly relevant to Google DeepMind Polaris evaluation-to-training feedback loop. |
| **OpenAI Sol 6.1** | *(In Progress)* ([`codex-sol-6-1-xhigh`](experiments/codex-sol-6-1-xhigh/))<br>Testing via Codex CLI with `xhigh` | *(In Progress)* ([`autobyteus-sol-6-1-xhigh`](experiments/autobyteus-sol-6-1-xhigh/))<br>Testing via AutoByteus Runtime | Evaluating OpenAI's flagship reasoning model against boundary leakage. |

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
├── claude-code-opus-5-5-xhigh/                # Ready for Opus 5.5 native run
│   └── README.md
├── autobyteus-opus-5-5-xhigh/                 # Ready for Opus 5.5 AutoByteus run
│   └── README.md
│
├── google-harness-astra-gemini-xhigh/         # Ready for Astra / Gemini native run
│   └── README.md
├── autobyteus-astra-gemini-xhigh/              # Ready for Astra / Gemini AutoByteus run
│   └── README.md
│
├── codex-sol-6-1-xhigh/                       # Ready for Sol 6.1 native run
│   └── README.md
└── autobyteus-sol-6-1-xhigh/                  # Ready for Sol 6.1 AutoByteus run
    └── README.md
```
