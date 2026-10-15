# Model Experiment: Claude Opus 5.5 (Thinking: xhigh)

This folder hosts the head-to-head empirical comparison for **Claude Opus 5.5** running with `thinking: xhigh` across two execution harnesses:

1. **[`native-harness/`](native-harness/)**: Anthropic Native Harness / Claude Code with Opus 5.5.
2. **[`autobyteus-runtime/`](autobyteus-runtime/)**: AutoByteus Autonomous Agent Runtime with Opus 5.5.

---

## Head-to-Head Comparison

| Evaluation Metric | Native Harness | AutoByteus Runtime |
| :--- | :--- | :--- |
| **Model** | Claude Opus 5.5 (`xhigh`) | Claude Opus 5.5 (`xhigh`) |
| **Class Modified** | *(Pending)* | *(Pending)* |
| **New Service Created?** | *(Pending)* | *(Pending)* |
| **Unit Test Outcome** | *(Pending)* | *(Pending)* |
| **Order Schema Forcing** | *(Pending)* | *(Pending)* |
| **Bypass Leakage** | *(Pending)* | *(Pending)* |
| **Overall Result** | *(Pending)* | *(Pending)* |

---

## How to Record Runs

- **Native Harness:** Save the agent session transcript and code diff in `native-harness/run-trace.md` and `native-harness/order_service.py`.
- **AutoByteus Runtime:** Save the design spec and generated files in `autobyteus-runtime/DESIGN.md` and `autobyteus-runtime/internal_billing_service.py`.
