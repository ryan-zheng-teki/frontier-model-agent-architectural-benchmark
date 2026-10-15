# Model Experiment: Claude Sonnet 5.5 (Thinking: xhigh)

This folder hosts the head-to-head empirical comparison for **Claude Sonnet 5.5** running with `thinking: xhigh` across two execution harnesses:

1. **[`native-harness/`](native-harness/)**: Anthropic Claude Code (vendor's official autonomous agent harness).
2. **[`autobyteus-runtime/`](autobyteus-runtime/)**: AutoByteus Autonomous Agent Runtime (principle-guided Solution Designer with architectural feedback loop).

---

## Head-to-Head Comparison

| Evaluation Metric | Native Harness (Claude Code) | AutoByteus Runtime |
| :--- | :--- | :--- |
| **Model** | Claude Sonnet 5.5 (`xhigh`) | Claude Sonnet 5.5 (`xhigh`) |
| **Class Modified** | `OrderService` (crammed batch billing inside) | None (`order_service.py` 100% untouched) |
| **New Service Created?** | No (kept all logic in `OrderService`) | Yes (`InternalBillingService`) |
| **Unit Test Outcome** | "All 16 unit tests pass" | Existing tests pass + new dedicated suite |
| **Order Schema Forcing** | **Yes:** forced dummy order check (`order exists`, `order is not PAID`) onto batch jobs | **No:** batch billing has no order dependency |
| **Bypass Leakage** | Leaked `process_internal_payment` to all `OrderService` callers (admitted in rationale) | Isolated exclusively at internal composition root |
| **Overall Result** | **FAIL** (Class bloat & schema-forcing) | **PASS** (Principle-guided clean refactor) |

---

## Key Research Takeaway

The exact same model (Sonnet 5.5 xhigh) produces radically different software architectures depending on the harness:
- Under **Claude Code**, the agent's reward signal is immediate task completion and making its test suite green (`pytest == 0`). To achieve this, it forced dummy order checks onto batch jobs and bloated `OrderService`.
- Under **AutoByteus Runtime**, the model is guided by structured architectural principles (Single Responsibility, clear boundary ownership, zero customer regression). It refused to edit `OrderService` and created an isolated, dedicated service.

**Conclusion:** The root cause of AI-generated codebase bloat is not model intelligence—it is the **evaluation & harness reward function**.
