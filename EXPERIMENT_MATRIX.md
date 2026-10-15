# Benchmark Experiment Matrix: Frontier Models × Harnesses

**Evaluation Setup:**
- All models evaluated with **`thinking: xhigh`** (maximum reasoning / chain-of-thought budget).
- Tested across two execution environments:
  1. **Vendor Native Harness:** The official autonomous coding agent / harness provided by the vendor (Anthropic Claude Code, OpenAI Codex CLI, Google Gemini CLI / AI Studio).
  2. **AutoByteus Runtime:** Autonomous principle-guided runtime with explicit architectural design principles, domain boundary enforcement, and solution review gates.

---

## The 2D Comparison Matrix

| Model (`thinking: xhigh`) | Vendor Native Harness | AutoByteus Runtime | Architectural Delta & Insight |
| :--- | :--- | :--- | :--- |
| **Claude Sonnet 5.5** | **FAIL**<br>• Crammed batch billing into `OrderService`<br>• "All 16 unit tests pass"<br>• Forced dummy order checks onto batch jobs<br>• Leaked bypass to customer wiring | **PASS**<br>• `order_service.py` untouched (0 regression)<br>• Created `InternalBillingService`<br>• Isolated at composition root<br>• No order dependency | **Same model, opposite architecture.** Proves that current agent harnesses incentivize test-hacking and class bloat over system health. |
| **Claude Opus 5.5** | *(In Progress)*<br>Testing via Claude Code with `xhigh` | *(In Progress)*<br>Testing via AutoByteus Runtime | Testing if increased raw model capacity alone overcomes the class-bloat trap without principle-guided runtime rules. |
| **Google Astra / Gemini** | *(In Progress)*<br>Testing via Google Native Harness with `xhigh` | *(In Progress)*<br>Testing via AutoByteus Runtime | Directly relevant to Google DeepMind Polaris evaluation-to-training feedback loop. |
| **OpenAI Sol 6.1** | *(In Progress)*<br>Testing via Codex CLI with `xhigh` | *(In Progress)*<br>Testing via AutoByteus Runtime | Evaluating OpenAI's flagship reasoning model against boundary leakage. |

---

## Detailed Directory Map

```text
experiments/
├── sonnet-5.5-xhigh/
│   ├── README.md                              # Detailed comparison & analysis
│   ├── native-harness/                        # Claude Code agent run
│   │   ├── run-trace.md                       # Execution transcript ("All 16 unit tests pass")
│   │   ├── direct-prompt-response.md          # Zero-shot prompt response
│   │   ├── order_service.py                   # Bloated class implementation
│   │   └── evaluation.md                      # Rubric analysis (Fail)
│   └── autobyteus-runtime/                    # AutoByteus Solution Designer
│       ├── DESIGN.md                          # Formal Design Spec SR-002
│       ├── internal_billing_service.py        # Independent, zero-regression service
│       └── evaluation.md                      # Rubric analysis (Pass)
│
├── opus-5.5-xhigh/
│   ├── README.md
│   ├── native-harness/                        # Ready for Opus 5.5 native run
│   └── autobyteus-runtime/                    # Ready for Opus 5.5 AutoByteus run
│
├── astra-gemini-xhigh/
│   ├── README.md
│   ├── native-harness/                        # Ready for Astra / Gemini native run
│   └── autobyteus-runtime/                    # Ready for Astra / Gemini AutoByteus run
│
└── sol-6.1-xhigh/
    ├── README.md
    ├── native-harness/                        # Ready for Sol 6.1 native run
    └── autobyteus-runtime/                    # Ready for Sol 6.1 AutoByteus run
```
